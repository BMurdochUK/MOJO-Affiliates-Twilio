"""
Functional UI tests for the MOJO web interface
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from flask import url_for
import time
import os

# Skip these tests if SKIP_SELENIUM_TESTS environment variable is set
pytestmark = pytest.mark.skipif(os.environ.get('SKIP_SELENIUM_TESTS') == '1',
                               reason="Skipping Selenium tests")

@pytest.fixture
def selenium_driver():
    """
    Set up a headless Chrome browser for UI testing
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        yield driver
    finally:
        if 'driver' in locals():
            driver.quit()

@pytest.fixture
def live_server(app):
    """
    Start a live Flask server for testing
    """
    # This would typically use LiveServer from pytest-flask
    # For this demo, we'll skip the actual implementation
    yield app

class TestUIFlow:
    """Test the main UI flows"""
    
    @pytest.mark.skip(reason="This is a demonstration test only")
    def test_dashboard_navigation(self, live_server, selenium_driver):
        """Test navigation on the dashboard"""
        # Get the dashboard
        selenium_driver.get(url_for('dashboard.index', _external=True))
        
        # Wait for the page to load
        WebDriverWait(selenium_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".stat-card"))
        )
        
        # Check that dashboard elements are present
        assert "Dashboard" in selenium_driver.title
        
        # Test navigation to templates
        selenium_driver.find_element(By.LINK_TEXT, "Templates").click()
        
        # Wait for templates page to load
        WebDriverWait(selenium_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        
        # Verify we're on the templates page
        assert "Templates" in selenium_driver.find_element(By.TAG_NAME, "h1").text
    
    @pytest.mark.skip(reason="This is a demonstration test only")
    def test_template_creation(self, live_server, selenium_driver):
        """Test creating a new template"""
        # Navigate to templates page
        selenium_driver.get(url_for('templates.index', _external=True))
        
        # Wait for the page to load
        WebDriverWait(selenium_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Click on "Create Template" button
        selenium_driver.find_element(By.LINK_TEXT, "Create Template").click()
        
        # Wait for form to load
        WebDriverWait(selenium_driver, 10).until(
            EC.presence_of_element_located((By.ID, "template-form"))
        )
        
        # Fill in the form
        selenium_driver.find_element(By.ID, "name").send_keys("Test Template")
        selenium_driver.find_element(By.ID, "template_sid").send_keys("HXTest123")
        selenium_driver.find_element(By.ID, "description").send_keys("This is a test template")
        
        # Submit the form
        selenium_driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Check for success message
        WebDriverWait(selenium_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )
        
        # Verify the template was created
        success_message = selenium_driver.find_element(By.CLASS_NAME, "alert-success").text
        assert "Template created successfully" in success_message 