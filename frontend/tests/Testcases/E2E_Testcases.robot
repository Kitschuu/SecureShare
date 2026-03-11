*** Settings ***
Library        SeleniumLibrary
Library        OperatingSystem
Library        Collections
Library        DateTime
Library        RequestsLibrary
Library        ../Resources/dotenv_helper.py
Resource       ../Resources/E2E_Resources.robot
Resource       ../Keywords/E2E_Keywords.robot

*** Test Cases ***
test_register_success
    Open CipherDrop WFE
    ${Auto_Username}=    Generate Auto Username
    ${Auto_Email}=    Generate Auto Email
    ${Auto_Password}=    Generate Auto Password
    Set Selenium Speed    0.20s
    Register WFE CipherDrop    ${Auto_Username}    ${Auto_Email}    ${Auto_Password}
    Verify Register successfully    ${Auto_Username}
    Login WFE CipherDrop    ${Auto_Username}    ${Auto_Password}
    Verify User Login successfully    ${Auto_Username}
    Logout WFE CipherDrop
    Close CipherDrop WFE
    [Teardown]    Clean Downloaded File    ${Auto_Username}_private_key.pem

test_register_duplicate
    Open CipherDrop WFE
    ${Auto_Username}=    Generate Auto Username
    ${Auto_Email}=    Generate Auto Email
    Set Selenium Speed    0.20s
    Register WFE CipherDrop    ${Sender_Username}    ${Sender_Email}    ${Sender_Password}
    Verify Register Duplicate
    Clear Input Register
    Register WFE CipherDrop    ${Auto_Username}    ${Sender_Email}    ${Sender_Password}
    Verify Register Duplicate
    Clear Input Register
    Register WFE CipherDrop    ${Sender_Username}    ${Auto_Email}    ${Sender_Password}
    Verify Register Duplicate
    Close CipherDrop WFE

test_login_success
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Sender_Username}    ${Sender_Password}
    Verify User Login successfully    ${Sender_Username}
    Verify JWT Token Received
    Logout WFE CipherDrop
    Close CipherDrop WFE

test_login_wrong_password
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Sender_Username}    5924998498
    Verify Login fail
    Close CipherDrop WFE

test_login_nonexistent_user
    Open CipherDrop WFE
    ${Auto_Username}=    Generate Auto Username
    ${Auto_Password}=    Generate Auto Password
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Auto_Username}    ${Auto_Password}
    Verify Login fail
    Close CipherDrop WFE

test_admin_can_access_stats
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Admin_Username}    ${Admin_Password}
    Verify Admin Login successfully    ${Admin_Username}
    ${admin_token}=    Get Access Token From Browser
    Call Admin Stats And Verify Status    ${admin_token}    200
    Click Admin Dashboard Page
    Logout WFE CipherDrop
    Close CipherDrop WFE

test_regular_user_blocked
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Sender_Username}    ${Sender_Password}
    Verify User Login successfully    ${Sender_Username}
    ${user_token}=    Get Access Token From Browser
    Call Admin Stats And Verify Status    ${user_token}    403
    Logout WFE CipherDrop
    Close CipherDrop WFE

test_encrypt_and_decrypt
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Sender_Username}    ${Sender_Password}
    Verify User Login successfully    ${Sender_Username}
    Click Share a File Page
    Select Recipient For Send File    ${Receiver_Username}
    Upload Files For Encryption    ${TestUpload2_filepath}    ${Sender_PrivateKey_filepath}
    Logout WFE CipherDrop
    Login WFE CipherDrop    ${Receiver_Username}    ${Receiver_Password}
    Verify User Login successfully    ${Receiver_Username}
    Click Secure Inbox Page
    Select File Inbox From Sender    ${TestUpload2_filename}    ${Sender_Username}
    Upload Private Key Files For Decryption    ${Receiver_PrivateKey_filepath}
    Verify Decrypt Success and Download    ${TestUpload2_filename}    ${TestUpload2_filename}
    Logout WFE CipherDrop
    Close CipherDrop WFE
    [Teardown]    Clean Downloaded File    ${TestUpload2_filename}

test_signature_wrong_key
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Sender_Username}    ${Sender_Password}
    Verify User Login successfully    ${Sender_Username}
    Click Share a File Page
    Select Recipient For Send File    ${Receiver_Username}
    Upload Files For Encryption    ${TestUpload2_filepath}    ${Receiver_PrivateKey_filepath}
    Logout WFE CipherDrop
    Login WFE CipherDrop    ${Receiver_Username}    ${Receiver_Password}
    Verify User Login successfully    ${Receiver_Username}
    Click Secure Inbox Page
    Select File Inbox From Sender    ${TestUpload2_filename}    ${Sender_Username}
    Upload Private Key Files For Decryption    ${Receiver_PrivateKey_filepath}
    Verify Decrypt Failed With Wrong Key
    Logout WFE CipherDrop
    Close CipherDrop WFE
    [Teardown]    Clean Downloaded File    ${TestUpload2_filename}

test_decrypt_wrong_key
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Sender_Username}    ${Sender_Password}
    Verify User Login successfully    ${Sender_Username}
    Click Share a File Page
    Select Recipient For Send File    ${Receiver_Username}
    Upload Files For Encryption    ${TestUpload2_filepath}    ${Sender_PrivateKey_filepath}
    Logout WFE CipherDrop
    Login WFE CipherDrop    ${Receiver_Username}    ${Receiver_Password}
    Verify User Login successfully    ${Receiver_Username}
    Click Secure Inbox Page
    Select File Inbox From Sender    ${TestUpload2_filename}    ${Sender_Username}
    Upload Private Key Files For Decryption    ${Sender_PrivateKey_filepath}
    Verify Decrypt Failed With Wrong Decryption Key
    Logout WFE CipherDrop
    Close CipherDrop WFE
    [Teardown]    Clean Downloaded File    ${TestUpload2_filename}

test_admin_integrity_check
    Open CipherDrop WFE
    Set Selenium Speed    0.20s
    Login WFE CipherDrop    ${Admin_Username}    ${Admin_Password}
    Verify Admin Login successfully    ${Admin_Username}
    ${admin_token}=    Get Access Token From Browser
    Call Admin Stats And Verify Status    ${admin_token}    200
    Click Admin Dashboard Page
    Click Refresh Stats Button
    Click Run Deep Integrity Check Button
    Click Load Recent Audit Trail Button
    Logout WFE CipherDrop
    Close CipherDrop WFE