"""
Automatic and interactive form detection and filling.

Detects form fields on a page and fills them using:
1. Environment variables from .env
2. JSON data from data/ folder
3. Interactive input (fallback)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from nlp2cmd.web_schema.form_data_loader import FormDataLoader


@dataclass
class FormField:
    """Represents a form field."""
    selector: str
    field_type: str  # text, email, password, textarea, select, checkbox, radio
    name: Optional[str] = None
    id: Optional[str] = None
    label: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    options: list[str] = field(default_factory=list)  # For select/radio
    
    def get_display_name(self) -> str:
        """Get human-readable field name."""
        return self.label or self.placeholder or self.name or self.id or "Unnamed field"


@dataclass
class FormData:
    """Collected form data."""
    fields: dict[str, str] = field(default_factory=dict)
    submit_selector: Optional[str] = None


class FormHandler:
    """
    Handles form detection and interactive filling.
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def detect_form_fields(self, page) -> list[FormField]:
        """
        Detect all form fields on a page.
        
        Args:
            page: Playwright page object
        
        Returns:
            List of FormField objects
        """
        fields = []
        
        # Detect input fields
        inputs = page.query_selector_all('input:not([type="hidden"]):not([type="submit"]):not([type="button"])')
        
        for inp in inputs:
            try:
                inp_type = inp.get_attribute('type') or 'text'
                name = inp.get_attribute('name')
                inp_id = inp.get_attribute('id')
                placeholder = inp.get_attribute('placeholder')
                required = inp.get_attribute('required') is not None
                
                # Try to find label
                label = None
                if inp_id:
                    label_elem = page.query_selector(f'label[for="{inp_id}"]')
                    if label_elem:
                        label = label_elem.inner_text().strip()
                
                # Generate selector
                if inp_id:
                    selector = f'#{inp_id}'
                elif name:
                    selector = f'input[name="{name}"]'
                else:
                    continue
                
                fields.append(FormField(
                    selector=selector,
                    field_type=inp_type,
                    name=name,
                    id=inp_id,
                    label=label,
                    placeholder=placeholder,
                    required=required,
                ))
            except Exception:
                continue
        
        # Detect textareas
        textareas = page.query_selector_all('textarea')
        
        for ta in textareas:
            try:
                name = ta.get_attribute('name')
                ta_id = ta.get_attribute('id')
                placeholder = ta.get_attribute('placeholder')
                required = ta.get_attribute('required') is not None
                
                # Try to find label
                label = None
                if ta_id:
                    label_elem = page.query_selector(f'label[for="{ta_id}"]')
                    if label_elem:
                        label = label_elem.inner_text().strip()
                
                # Generate selector
                if ta_id:
                    selector = f'#{ta_id}'
                elif name:
                    selector = f'textarea[name="{name}"]'
                else:
                    continue
                
                fields.append(FormField(
                    selector=selector,
                    field_type='textarea',
                    name=name,
                    id=ta_id,
                    label=label,
                    placeholder=placeholder,
                    required=required,
                ))
            except Exception:
                continue
        
        # Detect selects
        selects = page.query_selector_all('select')
        
        for sel in selects:
            try:
                name = sel.get_attribute('name')
                sel_id = sel.get_attribute('id')
                required = sel.get_attribute('required') is not None
                
                # Get options
                options = []
                option_elems = sel.query_selector_all('option')
                for opt in option_elems:
                    opt_text = opt.inner_text().strip()
                    if opt_text:
                        options.append(opt_text)
                
                # Try to find label
                label = None
                if sel_id:
                    label_elem = page.query_selector(f'label[for="{sel_id}"]')
                    if label_elem:
                        label = label_elem.inner_text().strip()
                
                # Generate selector
                if sel_id:
                    selector = f'#{sel_id}'
                elif name:
                    selector = f'select[name="{name}"]'
                else:
                    continue
                
                fields.append(FormField(
                    selector=selector,
                    field_type='select',
                    name=name,
                    id=sel_id,
                    label=label,
                    required=required,
                    options=options,
                ))
            except Exception:
                continue
        
        return fields
    
    def detect_submit_button(self, page) -> Optional[str]:
        """Detect form submit button."""
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Wyślij")',
            'button:has-text("Send")',
            'button:has-text("Prześlij")',
            'button:has-text("OK")',
        ]
        
        for selector in submit_selectors:
            try:
                elem = page.query_selector(selector)
                if elem:
                    return selector
            except Exception:
                continue
        
        return None
    
    def automatic_fill(
        self,
        fields: list[FormField],
        data_loader: Optional[FormDataLoader] = None,
    ) -> FormData:
        """
        Automatically fill form using data from .env and data/*.json files.
        
        Args:
            fields: List of detected form fields
            data_loader: Optional pre-configured FormDataLoader
        
        Returns:
            FormData with values from configuration files
        """
        loader = data_loader or FormDataLoader()
        form_data = FormData()
        
        # Skip internal/hidden-like fields (loaded from schema)
        skip_fields = loader.get_skip_fields() or {'sl', 'tl', 'query', 'gtrans', 'vote', 'honeypot', 'bot'}
        
        self.console.print("\n[cyan]📋 Auto-filling form fields:[/cyan]\n")
        
        table = Table()
        table.add_column("Field", style="yellow")
        table.add_column("Value", style="green")
        table.add_column("Source", style="dim")
        
        for f in fields:
            field_name_lower = (f.name or "").lower()
            
            # Skip internal/hidden-like fields
            if field_name_lower in skip_fields:
                continue
            
            # Handle checkbox fields (consent, RODO, etc.)
            if f.field_type == 'checkbox':
                # Check if we should auto-check this checkbox
                consent_value = loader.get_value_for_field(
                    field_name=f.name,
                    field_id=f.id,
                    field_label=f.label,
                    field_placeholder=f.placeholder,
                    field_type='checkbox',
                )
                # Also check for generic FORM_CONSENT
                if not consent_value:
                    consent_value = loader.get_env_value('FORM_CONSENT')
                
                if consent_value and consent_value.lower() in ('true', '1', 'yes', 'tak'):
                    form_data.fields[f.selector] = '__checkbox__'
                    table.add_row(
                        f.get_display_name()[:30],
                        "✓ (checked)",
                        ".env / data/",
                    )
                continue
            
            # Skip radio buttons for now
            if f.field_type == 'radio':
                continue
            
            # Get value from loader
            value = loader.get_value_for_field(
                field_name=f.name,
                field_id=f.id,
                field_label=f.label,
                field_placeholder=f.placeholder,
                field_type=f.field_type,
            )
            
            if value:
                form_data.fields[f.selector] = value
                table.add_row(
                    f.get_display_name(),
                    value[:40] + "..." if len(value) > 40 else value,
                    ".env / data/",
                )
        
        if form_data.fields:
            self.console.print(table)
        else:
            self.console.print("[yellow]No matching data found in .env or data/ files[/yellow]")
            self.console.print("[dim]Create .env with FORM_NAME, FORM_EMAIL, etc. or data/form_data.json[/dim]")
        
        return form_data
    
    def interactive_fill(
        self,
        fields: list[FormField],
        prefill: Optional[dict[str, str]] = None,
    ) -> FormData:
        """
        Interactively collect form data from user.
        
        Args:
            fields: List of detected form fields
            prefill: Optional prefilled values
        
        Returns:
            FormData with collected values
        """
        prefill = prefill or {}
        
        self.console.print("\n[cyan]📋 Form fields detected:[/cyan]\n")
        
        table = Table()
        table.add_column("#", style="cyan")
        table.add_column("Field", style="yellow")
        table.add_column("Type", style="dim")
        table.add_column("Required", style="red")
        
        for i, f in enumerate(fields, 1):
            req = "✓" if f.required else ""
            table.add_row(
                str(i),
                f.get_display_name(),
                f.field_type,
                req,
            )
        
        self.console.print(table)
        
        # Collect values
        form_data = FormData()
        
        self.console.print("\n[yellow]Enter values for each field (press Enter to skip):[/yellow]\n")
        
        for f in fields:
            field_name = f.get_display_name()
            
            # Check for prefill
            default = prefill.get(f.name or "") or prefill.get(f.id or "") or ""
            
            if f.field_type == 'select' and f.options:
                self.console.print(f"[dim]Options: {', '.join(f.options[:5])}[/dim]")
            
            prompt = f"[bold]{field_name}[/bold]"
            if f.required:
                prompt += " [red]*[/red]"
            if default:
                prompt += f" [{default}]"
            prompt += ": "
            
            value = self.console.input(prompt).strip()
            
            if not value and default:
                value = default
            
            if value:
                form_data.fields[f.selector] = value
        
        return form_data
    
    def fill_form(
        self,
        page,
        form_data: FormData,
        submit: bool = False,
    ) -> bool:
        """
        Fill form fields on page.
        
        Args:
            page: Playwright page object
            form_data: Form data to fill
            submit: Whether to submit the form
        
        Returns:
            True if successful
        """
        for selector, value in form_data.fields.items():
            try:
                elem = page.query_selector(selector)
                if not elem:
                    self.console.print(f"[yellow]Field not found: {selector}[/yellow]")
                    continue
                
                tag = elem.evaluate('el => el.tagName.toLowerCase()')
                inp_type = elem.get_attribute('type') or ''
                
                # Handle checkbox
                if inp_type == 'checkbox' or value == '__checkbox__':
                    is_checked = elem.is_checked()
                    if not is_checked:
                        elem.click()
                    page.wait_for_timeout(200)
                    self.console.print(f"[green]✓[/green] Checked: {selector}")
                    continue
                
                if tag == 'select':
                    elem.select_option(label=value)
                elif tag in ('input', 'textarea'):
                    elem.click()
                    elem.fill('')
                    elem.type(value, delay=30)
                
                page.wait_for_timeout(200)
                self.console.print(f"[green]✓[/green] Filled: {selector}")
                
            except Exception as e:
                self.console.print(f"[red]✗[/red] Error filling {selector}: {e}")
                return False
        
        if submit and form_data.submit_selector:
            try:
                page.click(form_data.submit_selector)
                page.wait_for_timeout(1000)
                self.console.print("[green]✓[/green] Form submitted")
            except Exception as e:
                self.console.print(f"[red]✗[/red] Submit error: {e}")
                return False
        
        return True
