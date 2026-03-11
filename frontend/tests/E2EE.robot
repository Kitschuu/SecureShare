*** Settings ***
Library        SeleniumLibrary
Library        Collections

*** Variables ***
${URL}         https://kitschuu-secureshare-frontendapp-lzx4q3.streamlit.app
${BROWSER}     chrome


*** Test Cases ***
test_register_success
    Open SecureShare WFE
    Close SecureShare WFE



*** Keywords ***
Open SecureShare WFE
    Open Browser    ${URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Implicit Wait    10s
    Wait Until Page Contains    SecureShare

Close SecureShare WFE
    Close Browser
