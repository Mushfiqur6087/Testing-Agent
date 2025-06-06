import os
import sys
from datetime import datetime

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from playwright.sync_api import sync_playwright
from src.browser.dom_tree_parser import DOMTreeParser

def run_demo(html_file: str) -> None:
    """Demo entry: load HTML, parse DOM, click login button, and print DOM tree."""
    # Create output file for analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(PROJECT_ROOT, "logs", f"dom_test_analysis_{timestamp}.txt")
    
    with open(output_file, 'w') as f:
        f.write("DOM Tree Parser Test Analysis\n")
        f.write("="*50 + "\n")
        f.write(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"HTML file: {html_file}\n\n")
        
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_file}")

            parser = DOMTreeParser(page)
            parser.parse()

            # Test 1: Initial DOM state
            initial_dom = parser.get_dom_string()
            print("\n=== DOM Tree (Initial State) ===")
            print(initial_dom)
            f.write("=== Test 1: Initial DOM State ===\n")
            f.write(initial_dom + "\n\n")

            # Test 2: Click login button without filling fields
            try:
                login_button = page.locator("button[type='submit']")
                if login_button.count() > 0:
                    print("\n=== Test 2: Clicking Login Button (Empty Fields) ===")
                    f.write("=== Test 2: Clicking Login Button (Empty Fields) ===\n")
                    login_button.click()
                    
                    # Wait for any changes
                    page.wait_for_timeout(1000)
                    
                    # Re-parse DOM after click
                    parser.parse()
                    
                    after_empty_click_dom = parser.get_dom_string()
                    print("\n=== DOM Tree (After Empty Click) ===")
                    print(after_empty_click_dom)
                    f.write(after_empty_click_dom + "\n\n")
                else:
                    error_msg = "\n❌ Login button not found!"
                    print(error_msg)
                    f.write(error_msg + "\n\n")
            except Exception as e:
                error_msg = f"\n❌ Error clicking login button: {e}"
                print(error_msg)
                f.write(error_msg + "\n\n")

            # Test 3: Fill valid credentials and test login
            try:
                print("\n=== Test 3: Testing with Valid Credentials ===")
                f.write("=== Test 3: Testing with Valid Credentials ===\n")
                
                # Fill email field
                email_field = page.locator("input[type='email']")
                email_field.fill("test@example.com")
                
                # Fill password field  
                password_field = page.locator("input[type='password']")
                password_field.fill("password123")
                
                print("✅ Filled credentials: test@example.com / password123")
                f.write("✅ Filled credentials: test@example.com / password123\n")
                
                # Click login button
                login_button.click()
                
                # Wait for changes to take effect
                page.wait_for_timeout(2000)
                
                # Re-parse DOM after successful login
                parser.parse()
                
                after_valid_login_dom = parser.get_dom_string()
                print("\n=== DOM Tree (After Valid Login) ===")
                print(after_valid_login_dom)
                f.write(after_valid_login_dom + "\n\n")
                
                # Check for success feedback
                feedback_div = page.locator("#feedback")
                if feedback_div.is_visible():
                    feedback_text = page.locator("#feedback-message").text_content()
                    success_msg = f"✅ Login feedback: {feedback_text}"
                    print(success_msg)
                    f.write(success_msg + "\n")
                
                # Check button text change
                button_text = login_button.text_content()
                button_msg = f"✅ Button text after login: {button_text}"
                print(button_msg)
                f.write(button_msg + "\n\n")
                
            except Exception as e:
                error_msg = f"\n❌ Error during valid login test: {e}"
                print(error_msg)
                f.write(error_msg + "\n\n")

            browser.close()
        
        f.write("="*50 + "\n")
        f.write("Test completed successfully!\n")
    
    print(f"\n📝 Analysis saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    demo_html = os.path.join(PROJECT_ROOT, "html", "login_form.html")
    output_file = run_demo(demo_html)
    print(f"🎉 Test completed! Check the analysis file: {output_file}")