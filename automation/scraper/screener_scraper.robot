*** Settings ***
Documentation     Extract Shareholding Pattern Details table from Screener.in
Library           SeleniumLibrary
Library           Collections
Library           String
Library           OperatingSystem

*** Variables ***
${BASE_URL}       https://www.screener.in/company
${BROWSER}        headlesschrome
# Using ID-based XPath is more reliable than absolute path, but points to the exact same element
${TABLE_CONTAINER_XPATH}    //div[@id='quarterly-shp']
${TABLE_XPATH}              ${TABLE_CONTAINER_XPATH}//table[contains(@class, 'data-table')]
${OUTPUT_DIR}               result
${STOCKS}                   TCS,INFY,RELIANCE,HDFCBANK

*** Test Cases ***
Extract Shareholding Pattern For All Stocks Sequentially
    [Documentation]    Opens a single browser tab and loops through stocks sequentially.
    [Setup]    Open Screener Browser Session
    ${stock_list}=    Evaluate    [s.strip() for s in ($STOCKS.split(',') if isinstance($STOCKS, str) else $STOCKS) if s.strip()]
    FOR    ${symbol}    IN    @{stock_list}
        Extract Stock Shareholding Pattern In Current Tab    ${symbol}
    END
    [Teardown]    Close Browser

*** Keywords ***
Extract Stock Shareholding Pattern In Current Tab
    [Arguments]    ${symbol}
    [Documentation]    Navigates to the stock URL in the open tab and extracts table data.
    ${url}=    Set Variable    ${BASE_URL}/${symbol}/consolidated/#shareholding
    ${output_file}=    Set Variable    ${OUTPUT_DIR}/${symbol}_shareholding_pattern.json
    
    Log To Console    \n[${symbol}] Navigating to ${url} in current tab...
    Go To    ${url}
    Log To Console    -> Waiting for table to appear in DOM (timeout: 20s)...
    Wait Until Page Contains Element    xpath=${TABLE_XPATH}    timeout=20s
    Log To Console    -> Scrolling table into view...
    Scroll Element Into View         xpath=${TABLE_XPATH}
    Sleep    1s
    Wait Until Element Is Visible    xpath=${TABLE_XPATH}    timeout=10s
    
    Log To Console    [${symbol}] Extracting column headers...
    ${headers}=    Get Table Headers
    
    Log To Console    [${symbol}] Extracting table rows...
    ${table_data}=    Get Table Rows Data
    
    Log To Console    [${symbol}] Saving to ${output_file}...
    Save Table Data To JSON    ${headers}    ${table_data}    ${output_file}

Open Screener Browser Session
    Log To Console    -> Configuring Chrome browser arguments...
    ${options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys
    Call Method    ${options}    add_argument    --no-sandbox
    Call Method    ${options}    add_argument    --disable-dev-shm-usage
    Call Method    ${options}    add_argument    --disable-gpu
    Call Method    ${options}    add_argument    --window-size\=1920,1080
    Call Method    ${options}    add_argument    --user-agent\=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
    ${is_headless}=    Evaluate    'headless' in '''${BROWSER}'''.lower() or not bool(__import__('os').environ.get('DISPLAY'))
    IF    ${is_headless}
        Log To Console    -> Headless environment detected: adding --headless=new...
        Call Method    ${options}    add_argument    --headless\=new
    END
    Log To Console    -> Launching Chrome browser session...
    Open Browser    about:blank    chrome    options=${options}
    Run Keyword And Ignore Error    Maximize Browser Window

Get Table Headers
    [Documentation]    Extracts column headers from the table thead.
    Log To Console    -> Querying table thead elements...
    ${header_elements}=    Get WebElements    xpath=${TABLE_XPATH}/thead/tr/th
    ${headers}=    Create List
    FOR    ${header_elem}    IN    @{header_elements}
        ${text}=    Get Text    ${header_elem}
        ${clean_text}=    Strip String    ${text}
        Append To List    ${headers}    ${clean_text}
    END
    ${header_count}=    Get Length    ${headers}
    Log To Console    -> Found ${header_count} header columns.
    ${first_header}=    Get From List    ${headers}    0
    IF    '${first_header}' == ''
        Set List Value    ${headers}    0    Category
    END
    RETURN    ${headers}

Get Table Rows Data
    [Documentation]    Extracts row categories and corresponding column values.
    ${row_elements}=    Get WebElements    xpath=${TABLE_XPATH}/tbody/tr
    ${total_rows}=      Get Length    ${row_elements}
    Log To Console    -> Found ${total_rows} rows in tbody.
    ${all_rows}=        Create List
    ${index}=           Set Variable    1

    FOR    ${row_elem}    IN    @{row_elements}
        ${cell_elements}=    Call Method    ${row_elem}    find_elements    xpath    .//td | .//th
        ${row_data}=         Create List
        
        FOR    ${cell_elem}    IN    @{cell_elements}
            ${raw_text}=    Get Text    ${cell_elem}
            ${cleaned_text}=    Replace String Using Regexp    ${raw_text}    [\\s\\+]+$    ${EMPTY}
            ${cleaned_text}=    Strip String    ${cleaned_text}
            Append To List      ${row_data}     ${cleaned_text}
        END
        
        ${row_length}=    Get Length    ${row_data}
        IF    ${row_length} == 0
            CONTINUE
        END
        
        ${category}=      Get From List    ${row_data}    0
        Log To Console    -> [Row ${index}/${total_rows}] Extracted: "${category}" (${row_data.__len__()} values)
        Append To List    ${all_rows}    ${row_data}
        ${index}=         Evaluate    ${index} + 1
    END
    RETURN    ${all_rows}

Save Table Data To JSON
    [Arguments]    ${headers}    ${table_data}    ${file_path}
    [Documentation]    Saves extracted table data to a formatted JSON file.
    Log To Console    -> Formatting and writing ${table_data.__len__()} rows to ${file_path}...
    ${directory}=    Evaluate    os.path.dirname(r'${file_path}') or '.'    modules=os
    Create Directory    ${directory}
    ${records}=    Evaluate    [dict(zip($headers, row)) for row in $table_data]
    ${json_payload}=    Create Dictionary    headers=${headers}    data=${records}
    ${json_string}=    Evaluate    json.dumps($json_payload, indent=2, ensure_ascii=False)    modules=json
    Create File    ${file_path}    ${json_string}    encoding=UTF-8
