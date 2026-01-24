"""
Web schema extractor - analyzes web pages and generates schemas.

Opcja B: Ekstrakcja schema przed interakcją ze stroną.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


@dataclass
class WebElement:
    """Represents an interactive element on a web page."""
    element_type: str  # input, button, link, textarea, select
    selector: str
    name: Optional[str] = None
    id: Optional[str] = None
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    text: Optional[str] = None
    input_type: Optional[str] = None
    role: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.element_type,
            "selector": self.selector,
            "name": self.name,
            "id": self.id,
            "aria_label": self.aria_label,
            "placeholder": self.placeholder,
            "text": self.text,
            "input_type": self.input_type,
            "role": self.role,
        }


@dataclass
class WebPageSchema:
    """Schema for a web page."""
    url: str
    domain: str
    title: str
    inputs: list[WebElement] = field(default_factory=list)
    buttons: list[WebElement] = field(default_factory=list)
    links: list[WebElement] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_appspec(self) -> dict[str, Any]:
        """Convert to app2schema.appspec format."""
        actions = []
        
        # Generate actions for inputs
        for inp in self.inputs:
            action_id = f"type_{inp.name or inp.id or 'input'}"
            actions.append({
                "id": action_id,
                "name": inp.aria_label or inp.placeholder or inp.name or "Type text",
                "description": f"Type text into {inp.element_type} field",
                "parameters": [
                    {
                        "name": "text",
                        "type": "string",
                        "description": "Text to type",
                        "required": True,
                    }
                ],
                "examples": [
                    f"wpisz tekst w {inp.aria_label or inp.name}",
                    f"type text in {inp.aria_label or inp.name}",
                ],
                "metadata": {
                    "selector": inp.selector,
                    "element_type": inp.element_type,
                    "input_type": inp.input_type,
                },
            })
        
        # Generate actions for buttons
        for btn in self.buttons:
            action_id = f"click_{btn.name or btn.id or 'button'}"
            actions.append({
                "id": action_id,
                "name": btn.text or btn.aria_label or "Click button",
                "description": f"Click {btn.text or 'button'}",
                "parameters": [],
                "examples": [
                    f"kliknij {btn.text}",
                    f"click {btn.text}",
                ],
                "metadata": {
                    "selector": btn.selector,
                    "element_type": btn.element_type,
                },
            })
        
        return {
            "app_name": self.domain,
            "app_version": "1.0",
            "description": f"Web interface for {self.domain}",
            "actions": actions,
            "metadata": {
                "url": self.url,
                "title": self.title,
                "extracted_at": self.metadata.get("extracted_at"),
                "total_inputs": len(self.inputs),
                "total_buttons": len(self.buttons),
                "total_links": len(self.links),
            },
        }
    
    def save(self, output_dir: Path) -> Path:
        """Save schema to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize domain for filename
        safe_domain = re.sub(r'[^\w\-.]', '_', self.domain)
        output_file = output_dir / f"{safe_domain}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_appspec(), f, indent=2, ensure_ascii=False)
        
        return output_file


class WebSchemaExtractor:
    """
    Extract schema from web pages using Playwright.
    
    Analyzes DOM structure to find interactive elements and generates
    app2schema.appspec compatible schemas.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
    
    def extract(self, url: str) -> WebPageSchema:
        """
        Extract schema from a web page.
        
        Args:
            url: URL to analyze
        
        Returns:
            WebPageSchema with extracted elements
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Playwright is required for web schema extraction")
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()
            
            # Navigate to page
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)  # Wait for dynamic content
            
            # Extract page info
            title = page.title()
            
            # Extract inputs
            inputs = self._extract_inputs(page)
            
            # Extract buttons
            buttons = self._extract_buttons(page)
            
            # Extract links
            links = self._extract_links(page)
            
            # Extract forms
            forms = self._extract_forms(page)
            
            browser.close()
        
        import datetime
        
        return WebPageSchema(
            url=url,
            domain=domain,
            title=title,
            inputs=inputs,
            buttons=buttons,
            links=links,
            forms=forms,
            metadata={
                "extracted_at": datetime.datetime.now().isoformat(),
            },
        )
    
    def _extract_inputs(self, page) -> list[WebElement]:
        """Extract input fields from page."""
        inputs = []
        
        # Get all input elements
        input_elements = page.query_selector_all('input, textarea')
        
        for i, elem in enumerate(input_elements):
            try:
                elem_type = elem.get_attribute('type') or 'text'
                
                # Skip hidden, submit, button inputs
                if elem_type in ('hidden', 'submit', 'button', 'image'):
                    continue
                
                name = elem.get_attribute('name')
                elem_id = elem.get_attribute('id')
                aria_label = elem.get_attribute('aria-label')
                placeholder = elem.get_attribute('placeholder')
                
                # Generate selector
                if elem_id:
                    selector = f"#{elem_id}"
                elif name:
                    selector = f"input[name='{name}'], textarea[name='{name}']"
                else:
                    selector = f"input:nth-of-type({i+1}), textarea:nth-of-type({i+1})"
                
                tag_name = elem.evaluate('el => el.tagName.toLowerCase()')
                
                inputs.append(WebElement(
                    element_type=tag_name,
                    selector=selector,
                    name=name,
                    id=elem_id,
                    aria_label=aria_label,
                    placeholder=placeholder,
                    input_type=elem_type,
                ))
            except Exception:
                continue
        
        return inputs
    
    def _extract_buttons(self, page) -> list[WebElement]:
        """Extract buttons from page."""
        buttons = []
        
        # Get all button elements
        button_elements = page.query_selector_all('button, input[type="submit"], input[type="button"], [role="button"]')
        
        for i, elem in enumerate(button_elements):
            try:
                name = elem.get_attribute('name')
                elem_id = elem.get_attribute('id')
                aria_label = elem.get_attribute('aria-label')
                text = elem.inner_text().strip() if elem.inner_text() else None
                role = elem.get_attribute('role')
                
                # Generate selector
                if elem_id:
                    selector = f"#{elem_id}"
                elif text:
                    selector = f"button:has-text('{text}'), [role='button']:has-text('{text}')"
                elif name:
                    selector = f"button[name='{name}']"
                else:
                    selector = f"button:nth-of-type({i+1})"
                
                buttons.append(WebElement(
                    element_type='button',
                    selector=selector,
                    name=name,
                    id=elem_id,
                    aria_label=aria_label,
                    text=text,
                    role=role,
                ))
            except Exception:
                continue
        
        return buttons
    
    def _extract_links(self, page) -> list[WebElement]:
        """Extract links from page (limited to important ones)."""
        links = []
        
        # Get navigation links
        link_elements = page.query_selector_all('nav a, header a, [role="navigation"] a')
        
        for i, elem in enumerate(link_elements[:20]):  # Limit to 20 links
            try:
                href = elem.get_attribute('href')
                text = elem.inner_text().strip() if elem.inner_text() else None
                aria_label = elem.get_attribute('aria-label')
                
                if not href or not text:
                    continue
                
                selector = f"a:has-text('{text}')"
                
                links.append(WebElement(
                    element_type='link',
                    selector=selector,
                    text=text,
                    aria_label=aria_label,
                ))
            except Exception:
                continue
        
        return links
    
    def _extract_forms(self, page) -> list[dict[str, Any]]:
        """Extract form structures."""
        forms = []
        
        form_elements = page.query_selector_all('form')
        
        for i, form in enumerate(form_elements):
            try:
                form_id = form.get_attribute('id')
                form_name = form.get_attribute('name')
                action = form.get_attribute('action')
                method = form.get_attribute('method') or 'get'
                
                # Get inputs in this form
                form_inputs = form.query_selector_all('input, textarea, select')
                input_names = [inp.get_attribute('name') for inp in form_inputs if inp.get_attribute('name')]
                
                forms.append({
                    "id": form_id,
                    "name": form_name,
                    "action": action,
                    "method": method,
                    "inputs": input_names,
                })
            except Exception:
                continue
        
        return forms


def extract_web_schema(
    url: str,
    output_dir: Optional[Path] = None,
    headless: bool = True,
    use_cache: bool = True,
) -> WebPageSchema:
    """
    Extract schema from a web page and optionally save it.
    
    Args:
        url: URL to analyze
        output_dir: Directory to save schema (if None, doesn't save)
        headless: Run browser in headless mode
        use_cache: Use cached browsers if available
    
    Returns:
        WebPageSchema
    """
    # Setup cache if requested
    if use_cache:
        try:
            from nlp2cmd.utils.external_cache import ExternalCacheManager
            cache_manager = ExternalCacheManager()
            cache_manager.setup_environment()
            
            # Install if needed
            if not cache_manager.is_playwright_cached():
                cache_manager.install_playwright_if_needed()
        except ImportError:
            pass  # Cache not available, continue normally
    
    extractor = WebSchemaExtractor(headless=headless)
    schema = extractor.extract(url)
    
    if output_dir:
        output_path = schema.save(Path(output_dir))
        print(f"Schema saved to: {output_path}")
    
    return schema
