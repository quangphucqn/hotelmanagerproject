
  // Hiển thị spinner khi trang chưa tải xong
  window.addEventListener('load', function() {
    // Ẩn spinner khi trang đã tải xong
    const spinner = document.querySelector('.lds-roller-container');
    spinner.style.display = 'none';
  });

