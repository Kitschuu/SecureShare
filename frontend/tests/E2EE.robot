*** Settings ***
Library        SeleniumLibrary
Library        OperatingSystem
Library        Collections
Library        DateTime

*** Variables ***
${URL}         https://kitschuu-secureshare-frontendapp-lzx4q3.streamlit.app
${BROWSER}     chrome

${Bill_Username}    bill
${Bill_Email}    bill@gmail.com
${Bill_Password}    bill1234

*** Test Cases ***
test_register_success
    Open SecureShare WFE
    ${Auto_Username}=    Generate Auto Username
    ${Auto_Email}=    Generate Auto Email
    ${Auto_Password}=    Generate Auto Password
    Set Selenium Speed    0.20s
    Register WFE SecureShare    ${Auto_Username}    ${Auto_Email}    ${Auto_Password}
    Verify Register successfully    ${Auto_Username}
    Login WFE SecureShare    ${Auto_Username}    ${Auto_Password}
    Verify Login successfully    ${Auto_Username}
    Close SecureShare WFE

test_register_duplicate
    Open SecureShare WFE
    ${Auto_Username}=    Generate Auto Username
    ${Auto_Email}=    Generate Auto Email
    Set Selenium Speed    0.20s
    Register WFE SecureShare    ${Bill_Username}    ${Bill_Email}    ${Bill_Password}
    Verify Register Duplicate
    Clear Input Register
    Register WFE SecureShare    ${Auto_Username}    ${Bill_Email}    ${Bill_Password}
    Verify Register Duplicate
    Clear Input Register
    Register WFE SecureShare    ${Bill_Username}    ${Auto_Email}    ${Bill_Password}
    Verify Register Duplicate
    Close SecureShare WFE

test_login_success
    Open SecureShare WFE
    Login WFE SecureShare    ${Bill_Username}    ${Bill_Password}
    Verify Login successfully    ${Bill_Username}
    Verify JWT Token Received
    Close SecureShare WFE

test_login_wrong_password
    Open SecureShare WFE
    Login WFE SecureShare    ${Bill_Username}    5924998498
    Verify Login fail
    Close SecureShare WFE

test_login_nonexistent_user
    Open SecureShare WFE
    ${Auto_Username}=    Generate Auto Username
    ${Auto_Password}=    Generate Auto Password
    Login WFE SecureShare    ${Auto_Username}    ${Auto_Password}
    Verify Login fail
    Close SecureShare WFE



*** Keywords ***
Open SecureShare WFE
    ${download_path}    Set Variable    ${EXECDIR}${/}downloads
    Create Directory    ${download_path}

    ${prefs} =    Create Dictionary    download.default_directory=${download_path}    download.prompt_for_download=${False}    directory_upgrade=${True}
    ${options} =    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Call Method    ${options}    add_experimental_option    prefs    ${prefs}
    
    Create Webdriver    Chrome    options=${options}
    Go To    ${URL}
    Maximize Browser Window
    Wait Until Page Contains    SecureShare

Login WFE SecureShare
    [Arguments]    ${Username}    ${Password}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//button[@data-testid="stTab"]//p[text()="Login"]    timeout=10s
    Click Element    xpath=//button[@data-testid="stTab"]//p[text()="Login"]   
    Sleep    2s
    Wait Until Page Contains    Login
    Wait Until Page Contains    Username
    Wait Until Page Contains    Password
    Wait Until Element Is Visible    xpath=//input[@aria-label="Username"]    timeout=10s
    Input Text    xpath=//input[@aria-label="Username"]    ${Username}
    Wait Until Element Is Visible    xpath=//input[@aria-label="Password"]    timeout=10s
    Input Password    xpath=//input[@aria-label="Password"]    ${Password}
    Click Element    xpath=//div[@data-testid="stButton"]//button[contains(., "Login")]
    Unselect Frame

Verify Login successfully
    [Arguments]    ${Username}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//*[@data-testid="stSidebar"]//*[contains(text(), "Welcome, ${Username}!")]    timeout=15s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stSidebar"]//p[contains(., "Role: User")]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Share a File"]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Secure Inbox"]    timeout=5s
    Wait Until Element Is Visible    xpath=//*[@data-testid="stSidebar"]//button[contains(., "Logout")]    timeout=5s
    Unselect Frame

Verify Login fail
    [Arguments]
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "Invalid credentials")]    timeout=15s
    Wait Until Page Contains Element    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "Invalid credentials")]    timeout=5s
    Unselect Frame

Verify JWT Token Received
    ${token}=    Execute Javascript    return window.localStorage.getItem('access_token');
    Should Not Be Empty    ${token}    msg=ไม่พบ JWT Token ใน Local Storage!
    Should Contain         ${token}    .
    Log    ✅ ได้รับ JWT Token สำเร็จ: ${token}

Register WFE SecureShare
    [Arguments]    ${Username}    ${Email}    ${Password}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//button[@data-testid="stTab"]//p[text()="Register"]    timeout=10s
    Click Element    xpath=//button[@data-testid="stTab"]//p[text()="Register"]

    Wait Until Element Is Visible    xpath=//div[contains(@class, 'st-key-reg_email')]//input    timeout=10s
    Input Text        xpath=//div[contains(@class, 'st-key-reg_user')]//input     ${Username}
    Input Text        xpath=//div[contains(@class, 'st-key-reg_email')]//input    ${Email}
    Input Password    xpath=//div[contains(@class, 'st-key-reg_pass')]//input     ${Password}

    Click Element     xpath=//div[@data-testid="stButton"]//button[contains(., "Register")]
    Unselect Frame

Clear Input Register
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[contains(@class, 'st-key-reg_email')]//input    timeout=10s
    Set Selenium Speed    0s
    Press Keys    xpath=//div[contains(@class, 'st-key-reg_user')]//input    CTRL+A    BACKSPACE
    Press Keys    xpath=//div[contains(@class, 'st-key-reg_email')]//input    CTRL+A    BACKSPACE
    Press Keys    xpath=//div[contains(@class, 'st-key-reg_pass')]//input    CTRL+A    BACKSPACE
    Unselect Frame
    Set Selenium Speed    0.25s

Verify Register successfully
    [Arguments]    ${Username}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentSuccess"]//p[text()="User registered successfully."]    timeout=15s
    Wait Until Page Contains Element    xpath=//div[@data-testid="stAlertContentWarning"]//p[contains(text(), "SAVE THIS PRIVATE KEY NOW")]    timeout=5s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stDownloadButton"]//button    timeout=5s
    Click Element     xpath=//div[@data-testid="stDownloadButton"]//button
    Sleep    2s
    Verify Downloaded Private Key    ${Username}
    Wait Until Element Is Not Visible    xpath=//div[@data-testid="stAlertContentSuccess"]//p[text()="User registered successfully."]    timeout=15s
    Wait Until Page Does Not Contain Element    xpath=//div[@data-testid="stAlertContentWarning"]//p[contains(text(), "SAVE THIS PRIVATE KEY NOW")]    timeout=5s
    Wait Until Element Is Not Visible    xpath=//div[@data-testid="stDownloadButton"]//button    timeout=5s
    Unselect Frame

Verify Register Duplicate
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    Set Selenium Speed    0s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "Username or email already registered")]    timeout=15s
    Page Should Not Contain Element  xpath=//div[@data-testid="stAlertContentSuccess"]
    Page Should Not Contain Element  xpath=//div[@data-testid="stAlertContentWarning"]
    Page Should Not Contain Element  xpath=//div[@data-testid="stDownloadButton"]
    Set Selenium Speed    0.20s
    Unselect Frame

Verify Downloaded Private Key
    [Arguments]    ${Username}
    
    ${expected_file}    Set Variable    ${EXECDIR}${/}downloads${/}${Username}_private_key.pem
    
    Wait Until Created    ${expected_file}    timeout=10s
    
    ${file_size}          Get File Size       ${expected_file}
    Should Be True        ${file_size} > 0

    Log    ✅ ดาวน์โหลดสำเร็จที่: ${expected_file}

Generate Auto Username
    ${Username}    Evaluate    "auto_user_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")    modules=datetime
    Return From Keyword    ${Username}

Generate Auto Email
    ${Email}    Evaluate    "auto_email_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "@gmail.com"    modules=datetime
    Return From Keyword    ${Email}

Generate Auto Password
    ${Password}    Evaluate    "auto_password_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")    modules=datetime
    Return From Keyword    ${Password}

Close SecureShare WFE
    Close Browser
