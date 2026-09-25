*** Settings ***
Documentation     Phase 1: Groww Login Flow Automation
Library           SeleniumLibrary

*** Variables ***
${URL}            https://groww.in
${BROWSER}        chrome
${EMAIL}          user_email@example.com    # Replace with user provided email or pass via command line
${PASSWORD}       user_password             # Pass via command line
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
    [Teardown]    Close Browser

*** Keywords ***
Initialize Automation Environment
    Set Screenshot Directory    ${SCREENSHOT_DIR}
    Open Browser    ${URL}    ${BROWSER}    options=add_argument("--headless"); add_argument("--no-sandbox"); add_argument("--disable-dev-shm-usage")
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

Step 5: Input Password
    ${password_present}=    Run Keyword And Return Status    Wait Until Element Is Visible    xpath=//*[@id="login_password1"]    timeout=10s
    IF    ${password_present}
        Input Text    xpath=//*[@id="login_password1"]    ${PASSWORD}
        Click Element    xpath=//*[@id="root"]/div[1]/div[1]/div[1]/div[2]/div/div/div/div[2]/div/div/div[4]/button
        Capture Page Screenshot    step5_password_submitted.png
    END

Step 6: Handle OTP Verification
    ${otp_present}=    Run Keyword And Return Status    Wait Until Element Is Visible    xpath=//input[contains(@id, "otp") or @type="number" or contains(@placeholder, "OTP")]    timeout=10s
    IF    ${otp_present}
        ${otp}=    Evaluate    input("\\n[ACTION REQUIRED] Please enter the OTP sent to your email/mobile: ")
        Input Text    xpath=//input[contains(@id, "otp") or @type="number" or contains(@placeholder, "OTP")]    ${otp}
        Wait Until Element Is Visible    xpath=//button[contains(., "Submit") or contains(., "Verify") or contains(., "Proceed")]    timeout=5s
        Click Element    xpath=//button[contains(., "Submit") or contains(., "Verify") or contains(., "Proceed")]
        Capture Page Screenshot    step5_otp_submitted.png
    END