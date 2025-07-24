// Hàm lấy CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

document.addEventListener('DOMContentLoaded', function() {
    // === Các biến DOM cho Popup ===
    const loginPopup = document.getElementById('loginPopup');
    const registerPopup = document.getElementById('registerPopup');

    const openLoginPopupBtn = document.getElementById('openLoginPopupBtn');
    const closeLoginPopupBtn = document.getElementById('closeLoginPopupBtn');
    const switchToRegisterBtn = document.getElementById('switchToRegisterBtn');

    const closeRegisterPopupBtn = document.getElementById('closeRegisterPopupBtn');
    const switchToLoginBtn = document.getElementById('switchToLoginBtn');
    
    const ajaxRegisterForm = document.getElementById('ajaxRegisterForm');
    const ajaxLoginForm = document.getElementById('ajaxLoginForm');
    const ajaxLogoutBtn = document.getElementById('ajaxLogoutBtn');

    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    const confirmDeletePopup = document.getElementById('confirmDeletePopup');
    const closeConfirmDeletePopupBtn = document.getElementById('closeConfirmDeletePopupBtn');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteForm = document.getElementById('confirmDeleteForm');
    const confirmDeleteMessage = document.getElementById('confirmDeleteMessage');

    // === Xử lý hiển thị Popup ===
    if (openLoginPopupBtn && loginPopup) {
        openLoginPopupBtn.onclick = function() {
            clearAllFormMessagesAndErrors(); // Xóa lỗi/message cũ khi mở popup
            loginPopup.style.display = 'flex';
        }
    }

    if (closeLoginPopupBtn && loginPopup) {
        closeLoginPopupBtn.onclick = function() { loginPopup.style.display = 'none'; }
    }
    if (switchToRegisterBtn && loginPopup && registerPopup) {
        switchToRegisterBtn.onclick = function(e) {
            e.preventDefault();
            clearAllFormMessagesAndErrors();
            loginPopup.style.display = 'none';
            registerPopup.style.display = 'flex';
        }
    }
    if (closeRegisterPopupBtn && registerPopup) {
        closeRegisterPopupBtn.onclick = function() { registerPopup.style.display = 'none'; }
    }
    if (switchToLoginBtn && loginPopup && registerPopup) {
        switchToLoginBtn.onclick = function(e) {
            e.preventDefault();
            clearAllFormMessagesAndErrors();
            registerPopup.style.display = 'none';
            loginPopup.style.display = 'flex';
        }
    }
    window.onclick = function(event) {
        if (loginPopup && event.target == loginPopup) { loginPopup.style.display = "none"; }
        if (registerPopup && event.target == registerPopup) { registerPopup.style.display = "none"; }
    }

    // Hàm helper để xóa tất cả các thông báo và lỗi form trong các popup
    function clearAllFormMessagesAndErrors() {
        document.querySelectorAll('.popup-message-ajax').forEach(el => el.textContent = '');
        document.querySelectorAll('.form-errors-ajax').forEach(el => el.innerHTML = '');
        document.querySelectorAll('.form-group .invalid-feedback-ajax').forEach(el => el.remove());
    }


    // === AJAX cho Form Đăng Ký ===
    if (ajaxRegisterForm) {
        ajaxRegisterForm.addEventListener('submit', function(event) {
            event.preventDefault(); 
            const currentFormElement = this; // 'this' là ajaxRegisterForm

            // Xóa message cũ và lỗi trường cũ từ currentFormElement
            showPopupMessage(currentFormElement.closest('.popup-content'), '', true); // Xóa message cũ
            displayAjaxFormErrors(currentFormElement, {}, null); // Xóa lỗi trường cũ

            const actionUrl = currentFormElement.dataset.actionUrl;
            if (!actionUrl) {
                console.error('Registration form action URL is not set!');
                showPopupMessage(currentFormElement.closest('.popup-content'), 'Lỗi cấu hình form (URL).', false);
                return;
            }

            const formData = new FormData(currentFormElement);
            const submitButton = currentFormElement.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.textContent = 'Đang xử lý...';
            submitButton.disabled = true;

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json().then(data => ({status: response.status, body: data}))
                .catch(err => { // Xử lý trường hợp response không phải JSON (ví dụ lỗi 500 HTML)
                    console.error("Failed to parse JSON response or non-JSON error", err, response);
                    throw new Error(`Lỗi server hoặc phản hồi không hợp lệ. Status: ${response.status} ${response.statusText}`);
                })
            )
            .then(({status, body}) => {
                if(submitButton){ submitButton.textContent = originalButtonText; submitButton.disabled = false; }

                if (status === 200 && body.success) {
                    showPopupMessage(currentFormElement.closest('.popup-content'), body.message, true);
                    if (body.auto_logged_in) {
                         setTimeout(() => { window.location.reload(); }, 1500);
                    } else {
                         setTimeout(() => {
                            if(registerPopup) registerPopup.style.display = 'none';
                            if(loginPopup) {
                                clearAllFormMessagesAndErrors(); // Xóa lỗi/message cũ của login popup trước khi mở
                                loginPopup.style.display = 'flex';
                            }
                            currentFormElement.reset();
                        }, 1500);
                    }
                } else { // Lỗi validation từ server (status 400) hoặc success: false
                    if (body.errors && Object.keys(body.errors).length > 0) {
                        displayAjaxFormErrors(currentFormElement, body.errors, submitButton);
                    } else { 
                        showPopupMessage(currentFormElement.closest('.popup-content'), body.message || 'Đăng ký thất bại. Vui lòng thử lại.', false);
                    }
                }
            })
            .catch(errorInfo => {
                console.error('Error during registration fetch:', errorInfo);
                let messageToShow = 'Không thể gửi yêu cầu. Vui lòng kiểm tra lại đường truyền.';
                if (errorInfo instanceof Error && errorInfo.message) { // Lỗi từ throw new Error
                    messageToShow = errorInfo.message;
                } else if (errorInfo && errorInfo.body && errorInfo.body.message) { // Lỗi có cấu trúc từ server (ít khi vào đây nếu đã throw)
                     messageToShow = errorInfo.body.message;
                }
                showPopupMessage(currentFormElement.closest('.popup-content'), messageToShow, false);
                if(submitButton){ submitButton.textContent = originalButtonText; submitButton.disabled = false; }
            });
        });
    }

    // === AJAX cho Form Đăng Nhập ===
    if (ajaxLoginForm) {
        ajaxLoginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const currentFormElement = this; // 'this' là ajaxLoginForm

            // Xóa message cũ và lỗi cũ
            showPopupMessage(currentFormElement.closest('.popup-content'), '', true);
            displayAjaxFormErrors(currentFormElement, {}, null);

            const actionUrl = currentFormElement.dataset.actionUrl;
            if (!actionUrl) {
                console.error('Login form action URL is not set via data-action-url!');
                showPopupMessage(currentFormElement.closest('.popup-content'), 'Lỗi cấu hình form (URL login).', false);
                return;
            }

            const formData = new FormData(currentFormElement);
            const submitButton = currentFormElement.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.textContent = 'Đang xử lý...';
            submitButton.disabled = true;

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json().then(data => ({status: response.status, body: data}))
                .catch(err => {
                    console.error("Failed to parse JSON response or non-JSON error (login)", err, response);
                    throw new Error(`Lỗi server hoặc phản hồi không hợp lệ. Status: ${response.status} ${response.statusText}`);
                })
            )
            .then(({status, body}) => {
                if(submitButton){ submitButton.textContent = originalButtonText; submitButton.disabled = false; }

                if (status === 200 && body.success) {
                    showPopupMessage(currentFormElement.closest('.popup-content'), body.message, true);
                    setTimeout(() => { window.location.reload(); }, 1000);
                } else { 
                    if (body.errors && body.errors.__all__ && body.errors.__all__.length > 0) {
                         displayAjaxFormErrors(currentFormElement, body.errors, submitButton); // AuthenticationForm lỗi thường ở __all__
                    } else if (body.message) {
                        showPopupMessage(currentFormElement.closest('.popup-content'), body.message, false);
                    } else {
                        showPopupMessage(currentFormElement.closest('.popup-content'), 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.', false);
                    }
                }
            })
            .catch(errorInfo => {
                console.error('Error during login fetch:', errorInfo);
                let messageToShow = 'Lỗi kết nối hoặc xử lý. Vui lòng thử lại.';
                if (errorInfo instanceof Error && errorInfo.message) {
                    messageToShow = errorInfo.message;
                }
                showPopupMessage(currentFormElement.closest('.popup-content'), messageToShow, false);
                if(submitButton){ submitButton.textContent = originalButtonText; submitButton.disabled = false; }
            });
        });
    }


    // === AJAX cho Đăng Xuất ===
    if (ajaxLogoutBtn) {
        ajaxLogoutBtn.addEventListener('click', function(event) {
            event.preventDefault();

            const logoutUrl = this.dataset.logoutUrl;
            if (!logoutUrl) {
                console.error('Logout URL is not set via data-logout-url!');
                alert('Lỗi cấu hình đăng xuất.');
                return;
            }

            fetch(logoutUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json().then(data => ({status: response.status, body: data}))
                .catch(err => {
                    console.error("Failed to parse JSON response or non-JSON error (logout)", err, response);
                    throw new Error(`Lỗi server hoặc phản hồi không hợp lệ khi đăng xuất. Status: ${response.status} ${response.statusText}`);
                })
            )
            .then(({status, body}) => {
                if (status === 200 && body.success) {
                    alert(body.message);
                    window.location.reload();
                } else {
                    console.error('Đăng xuất không thành công:', error);
                    //alert(body.message || 'Đăng xuất không thành công. Vui lòng thử lại.');
                }
            })
            .catch(error => {
                console.error('Error during logout fetch:', error);
                //alert(error.message || 'Lỗi kết nối khi đăng xuất. Vui lòng thử lại.');
            });
        });
    }


    // === Xử lý User Dropdown Menu ===
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function(event) {
            event.stopPropagation(); // Ngăn sự kiện click lan ra window
            userDropdown.classList.toggle('show');
            userMenuBtn.classList.toggle('active'); // Thêm/xóa class active cho button
        });

        // Đóng dropdown nếu click ra ngoài
        window.addEventListener('click', function(event) {
            if (!userMenuBtn.contains(event.target) && !userDropdown.contains(event.target)) {
                if (userDropdown.classList.contains('show')) {
                    userDropdown.classList.remove('show');
                    userMenuBtn.classList.remove('active');
                }
            }
        });
    }


    // === AJAX cho Đăng Xuất từ Dropdown ===
    const ajaxLogoutBtnTopNav = document.getElementById('ajaxLogoutBtnTopNav'); 
    if (ajaxLogoutBtnTopNav) {
        ajaxLogoutBtnTopNav.addEventListener('click', function(event) {
            event.preventDefault(); 

            const logoutUrl = this.dataset.logoutUrl; 
            if (!logoutUrl) {
                console.error('Logout URL (top nav) is not set via data-logout-url!');
                alert('Lỗi cấu hình đăng xuất.');
                return;
            }

            fetch(logoutUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken, // Đã có từ trên
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json().then(data => ({status: response.status, body: data}))
                .catch(err => {
                    console.error("Failed to parse JSON response or non-JSON error (logout top nav)", err, response);
                    throw new Error(`Lỗi server hoặc phản hồi không hợp lệ khi đăng xuất. Status: ${response.status} ${response.statusText}`);
                })
            )
            .then(({status, body}) => {
                if (status === 200 && body.success) {
                    // alert(body.message); // Có thể không cần alert, chỉ reload
                    window.location.reload(); // Tải lại trang để cập nhật UI
                } else {
                    alert(body.message || 'Đăng xuất không thành công. Vui lòng thử lại.');
                }
            })
            .catch(error => {
                console.error('Error during logout fetch (top nav):', error);
                alert(error.message || 'Lỗi kết nối khi đăng xuất. Vui lòng thử lại.');
            });
        });
    }

    // Hàm mở popup xác nhận xóa
    function openConfirmDeletePopup(deleteUrl,itemName) {
        if (confirmDeletePopup && confirmDeleteForm && confirmDeleteMessage) {
            confirmDeleteForm.action = deleteUrl;
            confirmDeleteMessage.textContent = `Bạn có chắc chắn muốn xóa "${itemName}"? Hành động này không thể hoàn tác.`;
            clearAllFormMessagesAndErrors();
            confirmDeletePopup.style.display = 'flex';
        }
    }

    // Gắn sự kiện cho tất cả các nút xóa bài viết (có class 'delete-post-btn')
    document.querySelectorAll('.action-btn.delete-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();

            const formElement = this.closest('form');
            if (formElement) {
                const deleteUrl = formElement.action;
                const postTitleElement = formElement.closest('tr').querySelector('td a'); // Tìm link tiêu đề trong cùng hàng
                const itemName = postTitleElement ? postTitleElement.title : "mục này";

                openConfirmDeletePopup(deleteUrl, itemName);
            } else {
                console.error("Không tìm thấy form cha cho nút xóa.");
            }
        });
    });

    if (closeConfirmDeletePopupBtn && confirmDeletePopup) {
        closeConfirmDeletePopupBtn.onclick = function() {
            confirmDeletePopup.style.display = 'none';
        }
    }

    if (cancelDeleteBtn && confirmDeletePopup) {
        cancelDeleteBtn.onclick = function() {
            confirmDeletePopup.style.display = 'none';
        }
    }

    // window.addEventListener('click', function(event) {
    //     if (confirmDeletePopup && event.target == confirmDeletePopup) {
    //         confirmDeletePopup.style.display = "none";
    //     }
    // });

    if (confirmDeleteForm) {
        confirmDeleteForm.addEventListener('submit', function(event) {
            const submitButton = this.querySelector('#confirmDeleteSubmitBtn');
            submitButton.textContent = 'Đang xóa...';
            submitButton.disabled = true;
        });
    }


    // === Xử lý Ẩn/Hiện Mật khẩu ===
    document.querySelectorAll('.toggle-password').forEach(toggle => {
        toggle.addEventListener('click', function () {
            const passwordInputWrapper = this.closest('.password-input-wrapper');
            if (passwordInputWrapper) {
                const passwordInput = passwordInputWrapper.querySelector('input');
                if (passwordInput && (passwordInput.type === "password" || passwordInput.type === "text")) {
                    if (passwordInput.type === "password") {
                        passwordInput.type = "text";
                        this.classList.remove('fa-eye');
                        this.classList.add('fa-eye-slash');
                    } else {
                        passwordInput.type = "password";
                        this.classList.remove('fa-eye-slash');
                        this.classList.add('fa-eye');
                    }
                }
            }
        });
    });

});


// Hàm helper để hiển thị message chung trong popup (không thay đổi)
function showPopupMessage(popupContentElement, message, isSuccess) {
    if (!popupContentElement) return; // Thoát nếu không tìm thấy popup content
    const messageDiv = popupContentElement.querySelector('.popup-message-ajax');
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.style.color = isSuccess ? 'green' : 'red';
        if (message) { // Chỉ set timeout nếu có message
            setTimeout(() => {
                messageDiv.textContent = '';
            }, 5000);
        }
    } else {
        // Fallback nếu không tìm thấy div message (ít khi xảy ra nếu HTML đúng)
        if (message) alert(message);
    }
}

// Hàm helper để hiển thị lỗi form (không thay đổi)
function displayAjaxFormErrors(formElement, errors, submitButton) {
    // Xóa các thông báo lỗi cũ trong popup
    const generalErrorContainer = formElement.querySelector('.form-errors-ajax');
    if (generalErrorContainer) generalErrorContainer.innerHTML = '';
    formElement.querySelectorAll('.form-group .invalid-feedback-ajax').forEach(el => el.remove());

    if (!errors || Object.keys(errors).length === 0) return;

    if (errors.__all__) {
        if (generalErrorContainer) {
             errors.__all__.forEach(error => {
                const p = document.createElement('p');
                p.textContent = error.message || error; 
                generalErrorContainer.appendChild(p);
            });
        } else { 
            errors.__all__.forEach(error => alert(error.message || error));
        }
    }
    for (const fieldName in errors) {
        if (fieldName !== '__all__') {
            const field = formElement.elements[fieldName];
            if (field && field.parentNode) { 
                let errorDiv = field.parentNode.querySelector('.invalid-feedback-ajax');
                if (!errorDiv) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback-ajax';
                    errorDiv.style.color = 'red';
                    errorDiv.style.fontSize = '0.9em';
                    errorDiv.style.marginTop = '5px';
                    field.parentNode.insertBefore(errorDiv, field.nextSibling);
                }
                errorDiv.innerHTML = ''; 
                errors[fieldName].forEach(error => {
                    const p = document.createElement('p');
                    p.textContent = error.message || error;
                    errorDiv.appendChild(p);
                });
            }
        }
    }
}