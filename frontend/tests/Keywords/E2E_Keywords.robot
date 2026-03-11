*** Settings ***
Library    OperatingSystem
Library    SeleniumLibrary
Library    RequestsLibrary
Library    file_checker.py


*** Keywords ***
Open CipherDrop WFE
    ${download_path}    Set Variable    ${EXECDIR}${/}frontend${/}tests${/}Keywords${/}downloads
    Create Directory    ${download_path}

    ${prefs} =    Create Dictionary    download.default_directory=${download_path}    download.prompt_for_download=${False}    directory_upgrade=${True}
    ${options} =    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Call Method    ${options}    add_experimental_option    prefs    ${prefs}
    
    Create Webdriver    Chrome    options=${options}
    Go To    ${URL}
    Maximize Browser Window
    Wait Until Page Contains    CipherDrop

Login WFE CipherDrop
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

Verify User Login successfully
    [Arguments]    ${Username}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//*[@data-testid="stSidebar"]//*[contains(text(), "Welcome, ${Username}!")]    timeout=15s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stSidebar"]//p[contains(., "Role: User")]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Share a File"]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Secure Inbox"]    timeout=5s
    Wait Until Element Is Visible    xpath=//*[@data-testid="stSidebar"]//button[contains(., "Logout")]    timeout=5s
    Unselect Frame

Verify Admin Login successfully
    [Arguments]    ${Username}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//*[@data-testid="stSidebar"]//*[contains(text(), "Welcome, ${Username}!")]    timeout=15s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stSidebar"]//p[contains(., "Role: Admin")]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Share a File"]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Secure Inbox"]    timeout=5s
    Wait Until Page Contains Element    xpath=//*[@data-testid="stRadio"]//p[text()="Admin Dashboard"]    timeout=5s
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
    Wait Until Keyword Succeeds    15s    2s    Check Access Token Cookie Exists
    ${cookie}=    Get Cookie    access_token
    ${token_value}=    Set Variable    ${cookie.value}
    ${clean_token}=    Evaluate    '${token_value}'.replace('"', '')
    Should Not Be Empty    ${clean_token}    msg=ค่า Token ใน Cookie ว่างเปล่า!
    Should Contain         ${clean_token}    .
    Return From Keyword    ${clean_token}

Check Access Token Cookie Exists
    ${cookie}=    Get Cookie    access_token
    Should Not Be Equal    ${cookie}    ${None}    msg=ไม่พบ Cookie ที่ชื่อ access_token!

Get Access Token From Browser
    Wait Until Keyword Succeeds    10s    1s    Get Cookie    access_token
    ${cookie}=    Get Cookie    access_token
    ${token_value}=    Set Variable    ${cookie.value}
    ${clean_token}=    Evaluate    '${token_value}'.replace('"', '')
    Return From Keyword    ${clean_token}

Call Admin Stats And Verify Status
    [Arguments]    ${token}    ${expected_status}
    ${headers}=    Create Dictionary    Authorization=Bearer ${token}
    ${cookies_dict}=    Create Dictionary    access_token=${token}
    Create Session    backend    ${BACKEND_API_URL}
    ${response}=      GET On Session    backend    /admin/stats    headers=${headers}    cookies=${cookies_dict}    expected_status=any
    Should Be Equal As Strings    ${response.status_code}    ${expected_status}


Register WFE CipherDrop
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
    ${expected_file}    Set Variable    ${EXECDIR}${/}frontend${/}tests${/}Keywords${/}downloads${/}${Username}_private_key.pem
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

Close CipherDrop WFE
    Close Browser

Select Recipient For Send File
    [Arguments]    ${recipient}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//input[@aria-label="Select Recipient"]    timeout=5s
    Click Element                    xpath=//input[@aria-label="Select Recipient"]
    Input Text                       xpath=//input[@aria-label="Select Recipient"]    ${recipient}
    Sleep    1s
    Press Keys    xpath=//input[@aria-label="Select Recipient"]    ENTER
    Sleep    0.5s
    Unselect Frame

Click Share a File Page
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    Click Element    xpath=//div[@data-testid="stRadio"]//p[text()="Share a File"]
    Wait Until Page Contains    Securely Share a File
    Unselect Frame

Click Secure Inbox Page
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    Click Element    xpath=//div[@data-testid="stRadio"]//p[text()="Secure Inbox"]
    Wait Until Page Contains    Your Secure Inbox
    Unselect Frame

Click Admin Dashboard Page
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    Click Element                    xpath=//div[@data-testid="stRadio"]//p[text()="Admin Dashboard"]
    Wait Until Page Contains         Security & Audit Dashboard    timeout=10s
    Unselect Frame

Click Refresh Stats Button
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    ${btn_xpath}=    Set Variable    xpath=//button[contains(., "Refresh Stats")]
    Wait Until Element Is Visible    ${btn_xpath}    timeout=10s
    Click Element                    ${btn_xpath}
    Sleep    5s
    Unselect Frame

Click Run Deep Integrity Check Button
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    ${btn_xpath}=    Set Variable    xpath=//button[contains(., "Run Deep Integrity Check")]
    Wait Until Element Is Visible    ${btn_xpath}    timeout=10s
    Click Element                    ${btn_xpath}
    Sleep    5s
    Unselect Frame

Click Load Recent Audit Trail Button
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    ${btn_xpath}=    Set Variable    xpath=//button[contains(., "Load Recent Audit Trail")]
    Wait Until Element Is Visible    ${btn_xpath}    timeout=10s
    Click Element                    ${btn_xpath}
    Sleep    5s
    Unselect Frame

Upload Files For Encryption
    [Arguments]    ${FilePath}    ${PrivateKeyPath}
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Choose File    xpath=//section[@aria-label="1. Choose a file to send"]//input[@type="file"]    ${FilePath}
    Choose File    xpath=//section[contains(@aria-label, "Private Key")]//input[@type="file"]    ${PrivateKeyPath}
    Sleep   10s
    Click Button    xpath=//button[contains(., "Encrypt & Send")]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentSuccess"]//p[contains(., "File encrypted, digitally signed, and securely sent!")]    timeout=15s
    Unselect Frame

Logout WFE CipherDrop
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//*[@data-testid="stSidebar"]//button[contains(., "Logout")]    timeout=10s
    Click Element    xpath=//*[@data-testid="stSidebar"]//button[contains(., "Logout")]
    Wait Until Page Contains    Login    timeout=10s
    Unselect Frame

Select File Inbox From Sender
    [Arguments]    ${filename}    ${sender}
    Wait Until Element Is Visible    xpath=//iframe[@title="streamlitApp"]    timeout=10s
    Select Frame                     xpath=//iframe[@title="streamlitApp"]
    ${expander_xpath}=    Set Variable    xpath=(//summary[contains(., "${filename}") and contains(., "${sender}")])[last()]
    Wait Until Element Is Visible    ${expander_xpath}    timeout=10s
    Click Element                    ${expander_xpath}
    Wait Until Element Is Visible    xpath=//details[@open]//div[@data-testid="stExpanderDetails"]    timeout=5s
    
    Unselect Frame

Upload Private Key Files For Decryption
    [Arguments]    ${PrivateKeyPath}
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    ${upload_xpath}=    Set Variable    xpath=//details[@open]//section[@aria-label="Upload your Private Key to Decrypt"]//input[@type="file"]
    Wait Until Page Contains Element    ${upload_xpath}    timeout=10s
    Choose File                         ${upload_xpath}    ${PrivateKeyPath}
    ${decrypt_btn}=     Set Variable    xpath=//details[@open]//button[contains(., "Verify Signature & Decrypt")]
    Wait Until Element Is Visible       ${decrypt_btn}     timeout=10s
    Click Element                       ${decrypt_btn}
    Unselect Frame

Verify Decrypt Success and Download
    [Arguments]    ${original_filename}    ${decrypted_filename}
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentSuccess"]//p[contains(., "Digital Signature Verified")]    timeout=15s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentSuccess"]//p[contains(., "File Decrypted Successfully")]    timeout=10s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stDownloadButton"]//p[contains(., "Download Original File")]    timeout=10s
    Click Element                    xpath=//div[@data-testid="stDownloadButton"]//button
    ${original_file_path}     Set Variable    ${EXECDIR}${/}frontend${/}tests${/}Resources${/}Updload_TestData${/}${original_filename}
    ${decrypted_file_path}    Set Variable    ${EXECDIR}${/}frontend${/}tests${/}Keywords${/}downloads${/}${decrypted_filename}
    Wait Until Created         ${decrypted_file_path}    timeout=30s
    Sleep    2s
    ${is_identical}=    Compare Files Integrity    ${original_file_path}    ${decrypted_file_path}
    Unselect Frame

Verify Decrypt Failed With Wrong Signature
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "TAMPER WARNING OR WRONG KEY!")]    timeout=15s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "Details: Invalid signature")]    timeout=5s
    Page Should Not Contain Element    xpath=//div[@data-testid="stDownloadButton"]//button
    Log    ✅ ยืนยันสำเร็จ: ระบบป้องกันการถอดรหัสและแจ้งเตือน Signature ผิดพลาดได้อย่างถูกต้อง
    Unselect Frame

Verify Decrypt Failed With Wrong Key
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "TAMPER WARNING OR WRONG KEY!")]    timeout=15s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "Details: Invalid signature")]    timeout=5s
    Page Should Not Contain Element    xpath=//div[@data-testid="stDownloadButton"]//button
    Unselect Frame

Verify Decrypt Failed With Wrong Decryption Key
    Select Frame    xpath=//iframe[@title="streamlitApp"]
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentSuccess"]//p[contains(., "Digital Signature Verified")]    timeout=15s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "TAMPER WARNING OR WRONG KEY!")]    timeout=5s
    Wait Until Element Is Visible    xpath=//div[@data-testid="stAlertContentError"]//p[contains(., "Details: Incorrect decryption")]    timeout=5s
    Page Should Not Contain Element    xpath=//div[@data-testid="stDownloadButton"]//button
    Unselect Frame

Clean Downloaded File
    [Arguments]    ${filename}
    Run Keyword And Ignore Error    Close CipherDrop WFE
    ${file_to_delete}=    Set Variable    ${EXECDIR}${/}frontend${/}tests${/}Keywords${/}downloads${/}${filename}
    Remove File    ${file_to_delete}
