# main.py
import sys
import json
from pathlib import Path
from agent.testing import perform_web_testing

test_map = {
    "1": "1_ParaBank.json",  # ParaBank – Web UI & API site. Online banking demo with login and REST/SOAP APIs.
                                # [Recommended] Need a site with web UI and APIs together? (1)
    "2": "2_RestfulBooker.json",  # Restful Booker – Web UI & API site. Bed & breakfast booking demo with React frontend and REST backend.
                                    # [Recommended] Need a site with web UI and APIs together? (2)
    "3": "3_AutomationPractiseWebsite.json",  # Automation Practice Website – Lifelike web UI site. Basic online store for UI tests.
                                                # [Recommended] Need a lifelike site? (3)
    "4": "4_Luma-Magento_eCommerce.json",  # Luma Magento eCommerce – Web UI site. Online store demo.
    "5": "5_DemoBlaze.json",  # Demoblaze – Web UI site. Basic online store for UI tests.
    "6": "6_swagLabs.json",  # Swag Labs – Web UI site. Online store with required login.
    "7": "7_AppliToolsDemoSite.json",  # Applitools demo site – Web UI site. Small site for visual testing demos.
                                        # [Recommended] Need to show visual testing? (7)
    "8": "8_AutomationBookstore.json",  # Automation Bookstore – Web UI site. One-page site for responsive design demos.
    "9": "9_JPetStoreDemo.json",  # JPetStore Demo – Web UI site. Pet store demo built with MyBatis/Spring.
    "10": "10_GlobalSQABankingProject.json",  # GlobalSQA Banking Project – Web UI site. Basic banking app with dropdown login.
    "11": "11_GatlingComputersDatabase.json",  # Gatling Computers Database – Web UI site. Paginated list of computers, filter/add.
    "12": "12_CandyMapper.json",  # CandyMapper – Web UI site. Halloween-themed bug demo.
    "13": "13_BulldoggyTheReminderApp.json",  # Bulldoggy: The Reminders App – DIY Web UI site. Local app with login/data (FastAPI+HTMX).
                                                # [Recommended] Need a local site with login and data? (13)
    "14": "14_OWASPJuiceShop.json",  # OWASP Juice Shop – DIY Web UI site. Security vulnerabilities demo (Node.js/Angular).
                                        # [Recommended] Need to show security vulnerabilities? (14)
    "15": "15_CypressRealWorldApp.json",  # Cypress Real-World App – DIY Web UI site. Fake payment app for Cypress testing.
    "16": "16_RealWorldExampleApp.json",  # RealWorld example apps – DIY Web UI site. Demo app in many frameworks.
    "17": "17_TheInternet.json",  # the-internet – Web UI elements. Practice interactions on elements.
                                    # [Recommended] Need to practice interactions on specific elements? (17)
    "18": "18_SeleniumTestPages.json",  # Selenium Test Pages – Web UI elements. Deeper examples for automation.
    "19": "19_LetCode.json",  # LetCode – Web UI elements. Clean pages and video tutorials for automation.
    "20": "20_DemoQA.json",  # DemoQA – Web UI elements. Practice site for elements, forms, frames, etc.
    "21": "21_UltimateQAAutomation.json",  # Ultimate QA Automation Practice – Web UI elements. Rich practice pages.
    "22": "22_UITestAutomation.json",  # UI Test Automation Playground – Web UI elements. Educational pages with interactable elements.
    "23": "23_SelectorsHubPractise.json",  # SelectorsHub Practice Page – Web UI elements. Practice page for selectors and elements.
    "24": "24_WebDriverUniversity.json",  # WebDriverUniversity.com – Web UI elements. Educational pages for automation.
    "25": "25_SauceLabsNativeSample.json",  # Sauce Labs Native Sample Application – DIY Mobile UI site. Mobile app demo for Android/iOS.
    "26": "26_JSONPlaceholder.json",  # JSONPlaceholder – API site. Public REST API for dummy data.
                                        # [Recommended] Need an API with dummy data? (26)
    "27": "27_SwaggerPetstore.json",  # Swagger Petstore – API site. Public REST API for pet store data.
    "28": "28_PublicAPI.json",  # Public APIs – API site. List of public APIs for testing.
    "29": "29_DeviceRegistry.json",  # Device Registry Service – DIY API site. Flask app for REST API testing.
                                    # [Recommended] Need to learn how to do REST API testing? (29)
    "30": "30_BestBuyAPI.json"  # Best Buy API Playground – DIY API site. REST API demo service from Best Buy.
}

# There are lots of demo sites above. Here are the ones I’d personally recommend for different needs:
# Need a site with web UI and APIs together? ParaBank (1) or Restful Booker (2)!
# Need a lifelike site? Automation Practice Website (3)!
# Need a local site with login and data? Bulldoggy: The Reminders App (13)!
# Need to show visual testing? Applitools demo site (7)!
# Need to show security vulnerabilities? OWASP Juice Shop (14)!
# Need to practice interactions on specific elements? the-internet (17)!
# Need an API with dummy data? JSONPlaceholder (26)!
# Need to learn how to do REST API testing? Device Registry Service (29)!

testFileNo = "1"

def parse_test_cases(file_path):
    """
    Parses the .json test file and extracts URL and test cases.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    url = data.get("URL")
    test_cases = data.get("TestCases", [])
    return url, test_cases

def main():
    testfile_name = test_map.get(testFileNo)
    print(f"[DEBUG] Selected test file: {testfile_name}")
    testfiles_dir = Path(__file__).parent / "TestFiles"
    print(f"[DEBUG] Test files directory: {testfiles_dir}")
    testfile = testfiles_dir / testfile_name

    url, test_cases = parse_test_cases(testfile)

    # First loop: print debug info for all test cases
    for case in test_cases:
        print(f"\n[DEBUG] URL: {url}")
        print(f"[DEBUG] Running Test: {case.get('Name')}")
        print(f"[DEBUG] Description: {case.get('Description')}")
        print(f"[DEBUG] Steps:")
        for idx, step in enumerate(case.get("Steps", []), 1):
            print(f"  Step {idx}: {step}")
        task_description = " ".join(case.get("Steps", []))
        print(f"[DEBUG] Task Description: {task_description}")

    # Second loop: execute test cases one by one
    for case in test_cases:
        task_description = " ".join(case.get("Steps", []))
        try:
            perform_web_testing(url, task_description)
        except Exception as e:
            print(f"[ERROR] Test case '{case.get('Name')}' failed with error: {e}")
            sys.exit(1)  # Stop execution if a test case fails

if __name__ == "__main__":
    main()