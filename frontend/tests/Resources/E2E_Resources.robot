*** Variables ***
${BACKEND_API_URL}      %{API_URL}
${URL}                  https://kitschuu-secureshare-frontendapp-lzx4q3.streamlit.app
${BROWSER}              chrome

${Sender_PrivateKey_filepath}            ${EXECDIR}${/}frontend${/}tests${/}Resources${/}PrivateKey_TestData${/}test_sender_private_key.pem
${Receiver_PrivateKey_filepath}          ${EXECDIR}${/}frontend${/}tests${/}Resources${/}PrivateKey_TestData${/}test_receiver_private_key.pem

${TestUpload_filepath}        ${EXECDIR}${/}frontend${/}tests${/}Resources${/}Updload_TestData${/}Ch-1.pdf
${TestUpload_filename}        Ch-1.pdf

${TestUpload2_filepath}        ${EXECDIR}${/}frontend${/}tests${/}Resources${/}Updload_TestData${/}Miniproject_circuit.png
${TestUpload2_filename}        Miniproject_circuit.png

${Sender_Username}      test_sender
${Sender_Email}         test_sender@gmail.com
${Sender_Password}      test_sender1234

${Receiver_Username}    test_receiver
${Receiver_Email}       test_receiver@gmail.com
${Receiver_Password}    test_receiver1234

${Admin_Username}       test_admin
${Admin_Email}          test_admin@gmail.com
${Admin_Password}       test_admin1234