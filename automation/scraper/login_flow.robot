*** Settings ***
Documentation     Phase 1: Groww Login Flow Automation
Library           SeleniumLibrary
Library           String
Library           OperatingSystem

*** Variables ***
${URL}            https://groww.in
${BROWSER}        chrome
${EMAIL}          user_email@example.com    # Replace with user provided email or pass via command line
${PASSWORD}       user_password             # Pass via command line
${PIN}            user_pin                  # Pass via command line
${SCREENSHOT_DIR}  ${CURDIR}/results/screenshot

*** Test Cases ***
Execute Groww Login Phase 1
    [Setup]    Initialize Automation Environment
    Step 1: Load Groww Website
    Step 2: Click Log In Button
    Step 3: Input Email Address
    Step 4: Click Continue Button
    Step 4.5: Input Password
    Step 5: Handle OTP Verification
    Step 6: Input Groww PIN
    Step 7: Navigate To Reports Section
    Step 8: Select Mutual Fund Holdings
    Step 9: Download Holdings File
    Step 10: Select Stocks Holdings
    Step 11: Download Stock Holdings File
    [Teardown]    Close Browser

*** Keywords ***
Initialize Automation Environment
    Set Screenshot Directory    ${SCREENSHOT_DIR}
    Create Directory    ${CURDIR}/reports
    Empty Directory    ${CURDIR}/reports
    ${prefs}=    Create Dictionary    download.default_directory=${CURDIR}/reports
    Open Browser    ${URL}    ${BROWSER}    options=add_argument("--headless=new"); add_argument("--window-size=1920,1080"); add_argument("--no-sandbox"); add_argument("--disable-dev-shm-usage"); add_experimental_option("prefs", ${prefs})
    Maximize Browser Window

Step 1: Load Groww Website
    Wait Until Page Contains Element    xpath=//div[@id="root"]    timeout=15s
    Capture Page Screenshot    step1_homepage_loaded.png

Step 2: Click Log In Button
    Wait Until Element Is Visible    xpath=//*[@id="root"]/div[1]/div[1]/div[2]/div[2]/button    timeout=10s
    Click Element    xpath=//*[@id="root"]/div[1]/div[1]/div[2]/div[2]/button
    Capture Page Screenshot    step2_login_modal_opened.png

Step 3: Input Email Address
    Wait Until Element Is Visible    id=login_email1    timeout=10s
    Input Text    id=login_email1    ${EMAIL}
    Capture Page Screenshot    step3_email_entered.png

Step 4: Click Continue Button
    Wait Until Element Is Visible    xpath=//*[@id="lils382InitialLoginScreen"]/div[3]/div[3]/button    timeout=10s
    Click Element    xpath=//*[@id="lils382InitialLoginScreen"]/div[3]/div[3]/button
    Capture Page Screenshot    step4_continue_clicked.png

Step 4.5: Input Password
    ${password_present}=    Run Keyword And Return Status    Wait Until Element Is Visible    xpath=//*[@id="login_password1"]    timeout=10s
    IF    ${password_present}
        Input Text    xpath=//*[@id="login_password1"]    ${PASSWORD}
        Click Element    xpath=//*[@id="root"]/div[1]/div[1]/div[1]/div[2]/div/div/div/div[2]/div/div/div[4]/button
        # Wait for the transition from the password screen to the OTP screen
        Sleep    5s
        Capture Page Screenshot    step4_5_password_submitted.png
    END

Step 5: Handle OTP Verification
    ${otp_present}=    Run Keyword And Return Status    Wait Until Element Is Visible    id=otpinput88parent    timeout=15s
    IF    ${otp_present}
        ${otp}=    Evaluate    [sys.__stdout__.write("\\n>>> [ACTION REQUIRED] Please enter the OTP: "), sys.__stdout__.flush(), sys.__stdin__.readline().strip()][2]    modules=sys
        # Convert string to list of characters
        @{digits}=    Split String To Characters    ${otp}
        FOR    ${index}    ${digit}    IN ENUMERATE    @{digits}
            ${input_index}=    Evaluate    ${index} + 1
            Input Text    xpath=(//div[@id="otpinput88parent"]//input)[${input_index}]    ${digit}
        END
        Capture Page Screenshot    step5_otp_submitted.png
        # Groww usually auto-submits once the 6th digit is entered. 
        # If not, add a 'Click Element' for the submit button here.
        Sleep    5s    # Wait for post-login redirect
    END

Step 6: Input Groww PIN
    # Extra wait to ensure the PIN modal and its JS are fully initialized
    Sleep    2s
    ${pin_present}=    Run Keyword And Return Status    Wait Until Element Is Visible    xpath=//div[contains(@class, "tfaep471PinInput")]    timeout=15s
    IF    ${pin_present}
        Wait Until Page Contains    Please Enter Groww PIN here    timeout=10s
        # Convert string to list of characters
        @{digits}=    Split String To Characters    ${PIN}
        FOR    ${index}    ${digit}    IN ENUMERATE    @{digits}
            ${input_index}=    Evaluate    ${index} + 1
            Input Text    xpath=(//div[contains(@class, "tfaep471PinInput")]//input)[${input_index}]    ${digit}
            Sleep    0.5s    # Small delay between digits to ensure JS handles input correctly
        END
        Capture Page Screenshot    step6_pin_submitted.png
        # Wait for the landing screen: the PIN modal should disappear automatically once the last digit is entered.
        Wait Until Element Is Not Visible    xpath=//div[contains(@class, "tfaep471PinInput")]    timeout=20s
    END

Step 7: Navigate To Reports Section
    # Click on the profile avatar to open the dropdown menu
    Wait Until Element Is Visible    xpath=//*[@id="root"]/div[1]/div/div[3]/div[2]/div[2]/div/div[1]/div/div/img    timeout=20s
    Click Element    xpath=//*[@id="root"]/div[1]/div/div[3]/div[2]/div[2]/div/div[1]/div/div/img
    Sleep    2s    # Wait for dropdown animation to complete
    # Select 'Reports' from the dropdown
    Wait Until Element Is Visible    xpath=//*[@id="reports"]/div[2]/div[1]    timeout=10s
    Click Element    xpath=//*[@id="reports"]/div[2]/div[1]
    Capture Page Screenshot    step7_reports_navigated.png

Step 8: Select Mutual Fund Holdings
    Wait Until Element Is Visible    xpath=//div[contains(@class, "reportCategory_reportItem") and contains(., "Mutual Funds - Holdings statement")]    timeout=20s
    Click Element    xpath=//div[contains(@class, "reportCategory_reportItem") and contains(., "Mutual Funds - Holdings statement")]
    Capture Page Screenshot    step8_mf_holdings_clicked.png

Step 9: Download Holdings File
    Wait Until Element Is Visible    xpath=//button[span[text()="Download"]]    timeout=20s
    # Use JavaScript click to bypass sticky layout containers or overlay screens intercepting standard clicks
    ${download_btn}=    Get WebElement    xpath=//button[span[text()="Download"]]
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${download_btn}
    Sleep    5s    # Wait for file download to conclude
    Capture Page Screenshot    step9_download_clicked.png
    Wait Until Keyword Succeeds    15s    1s    Check And Rename File    mutualfund.xlsx

Step 10: Select Stocks Holdings  
    Click Element    xpath=//div[contains(@class, "reportCategory_reportItem") and contains(., "Stocks - Holdings statement")]
    Capture Page Screenshot    step10_stock_holdings_clicked.png

Step 11: Download Stock Holdings File
    Wait Until Element Is Visible    xpath=//button[span[text()="Download"]]    timeout=20s
    # Use JavaScript click to bypass sticky layout containers or overlay screens intercepting standard clicks
    ${download_btn}=    Get WebElement    xpath=//button[span[text()="Download"]]
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${download_btn}
    Sleep    5s    # Wait for file download to conclude
    Capture Page Screenshot    step11_download_clicked.png
    Wait Until Keyword Succeeds    15s    1s    Check And Rename File    stock.xlsx

Check And Rename File
    [Arguments]    ${target_name}
    ${files}=    List Files In Directory    ${CURDIR}/reports
    ${found}=    Set Variable    ${FALSE}
    FOR    ${file}    IN    @{files}
        ${is_temp}=    Evaluate    '${file}'.endswith('.crdownload') or '${file}'.startswith('.com.google.Chrome')
        ${is_target}=    Evaluate    '${file}' == 'mutualfund.xlsx' or '${file}' == 'stock.xlsx'
        IF    not ${is_temp} and not ${is_target}
            Move File    ${CURDIR}/reports/${file}    ${CURDIR}/reports/${target_name}
            ${found}=    Set Variable    ${TRUE}
            Exit For Loop
        END
    END
    IF    not ${found}
        Fail    No downloaded file found to rename
    END