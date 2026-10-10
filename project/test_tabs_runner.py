import os
import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ARTIFACTS_DIR = r"C:\Users\wrich\.gemini\antigravity-ide\brain\efdb472b-fb69-4306-9398-40e23c39b776"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def run_tests():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    results = {}

    try:
        print("Navigating to http://127.0.0.1:8000...")
        driver.get("http://127.0.0.1:8000/")
        time.sleep(2)

        # 1. Landing Page
        p_landing = os.path.join(ARTIFACTS_DIR, "tab_test_0_landing.png")
        driver.save_screenshot(p_landing)
        results["landing"] = {"status": "ok", "screenshot": p_landing}
        print("Landing screenshot captured.")

        # Click Launch App
        launch_btn = driver.find_element(By.CSS_SELECTOR, ".btn-launch")
        launch_btn.click()
        time.sleep(1)

        # 2. Tab 1: Challenge GSTLens (Judge Mode)
        p_judge_a = os.path.join(ARTIFACTS_DIR, "tab_test_1_judge_invoice_a.png")
        driver.save_screenshot(p_judge_a)
        results["tab_judge_a"] = {"status": "ok", "screenshot": p_judge_a}
        print("Tab 1 (Invoice A) captured.")

        # Switch to Invoice B in Tab 1
        sc_b = driver.find_element(By.ID, "scCard_b")
        sc_b.click()
        time.sleep(1)
        p_judge_b = os.path.join(ARTIFACTS_DIR, "tab_test_1_judge_invoice_b.png")
        driver.save_screenshot(p_judge_b)
        results["tab_judge_b"] = {"status": "ok", "screenshot": p_judge_b}
        print("Tab 1 (Invoice B with repair timeline) captured.")

        # Switch to Invoice C in Tab 1
        sc_c = driver.find_element(By.ID, "scCard_c")
        sc_c.click()
        time.sleep(1)
        p_judge_c = os.path.join(ARTIFACTS_DIR, "tab_test_1_judge_invoice_c.png")
        driver.save_screenshot(p_judge_c)
        results["tab_judge_c"] = {"status": "ok", "screenshot": p_judge_c}
        print("Tab 1 (Invoice C with statutory conflict) captured.")

        # 3. Tab 2: Live Batch Pipeline
        tab_ws = driver.find_element(By.ID, "tabBtn_workspace")
        tab_ws.click()
        time.sleep(1)
        p_ws = os.path.join(ARTIFACTS_DIR, "tab_test_2_workspace_pipeline.png")
        driver.save_screenshot(p_ws)
        results["tab_workspace"] = {"status": "ok", "screenshot": p_ws}
        print("Tab 2 (Live Batch Pipeline) captured.")

        # 4. Tab 3: Side-by-Side Inspector
        tab_split = driver.find_element(By.ID, "tabBtn_split")
        tab_split.click()
        time.sleep(1)
        p_split = os.path.join(ARTIFACTS_DIR, "tab_test_3_side_by_side.png")
        driver.save_screenshot(p_split)
        results["tab_split"] = {"status": "ok", "screenshot": p_split}
        print("Tab 3 (Side-by-Side Inspector) captured.")

        # 5. Tab 4: Explainable Rules
        tab_rules = driver.find_element(By.ID, "tabBtn_rules")
        tab_rules.click()
        time.sleep(1)
        p_rules = os.path.join(ARTIFACTS_DIR, "tab_test_4_explainable_rules.png")
        driver.save_screenshot(p_rules)
        results["tab_rules"] = {"status": "ok", "screenshot": p_rules}
        print("Tab 4 (Explainable Rules) captured.")

        # 6. Tab 5: Financial Dashboard
        tab_fin = driver.find_element(By.ID, "tabBtn_financial")
        tab_fin.click()
        time.sleep(1)
        p_fin = os.path.join(ARTIFACTS_DIR, "tab_test_5_financial_dashboard.png")
        driver.save_screenshot(p_fin)
        results["tab_financial"] = {"status": "ok", "screenshot": p_fin}
        print("Tab 5 (Financial Dashboard) captured.")

        # 7. Tab 6: Cross-Invoice Anomalies
        tab_anom = driver.find_element(By.ID, "tabBtn_anomalies")
        tab_anom.click()
        time.sleep(1)
        p_anom = os.path.join(ARTIFACTS_DIR, "tab_test_6_cross_anomalies.png")
        driver.save_screenshot(p_anom)
        results["tab_anomalies"] = {"status": "ok", "screenshot": p_anom}
        print("Tab 6 (Cross-Invoice Anomalies) captured.")

        # 8. Modals: Certified Report Modal
        btn_report = driver.find_element(By.CSS_SELECTOR, ".btn-report-header")
        btn_report.click()
        time.sleep(1)
        p_report = os.path.join(ARTIFACTS_DIR, "tab_test_7_report_modal.png")
        driver.save_screenshot(p_report)
        results["report_modal"] = {"status": "ok", "screenshot": p_report}
        print("Certified Report Modal captured.")

        # Close report modal
        close_btn = driver.find_element(By.CSS_SELECTOR, "#reportModal .modal-close")
        close_btn.click()
        time.sleep(0.5)

        # 9. Return to Landing
        landing_nav_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Landing')]")
        landing_nav_btn.click()
        time.sleep(1)
        p_back_landing = os.path.join(ARTIFACTS_DIR, "tab_test_8_back_to_landing.png")
        driver.save_screenshot(p_back_landing)
        results["back_to_landing"] = {"status": "ok", "screenshot": p_back_landing}
        print("Back to Landing captured.")

        print("\nALL TABS TESTED SUCCESSFULLY!")
        print(json.dumps(results, indent=2))

    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
