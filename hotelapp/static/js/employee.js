$(document).ready(function () {
    // Chọn tất cả các nút có ID bắt đầu bằng "rental-button-"
    const rentalButtons = $('[id^="rental-button-"]');
    let currentForm = null; // Biến lưu form hiện tại

    rentalButtons.on("click", function (event) {
        event.preventDefault(); // Ngăn không gửi form ngay lập tức
        currentForm = $(this).closest('form'); // Lưu form hiện tại
        $("#confirmationModal").modal('show'); // Hiển thị modal
    });

    // Xử lý khi nhấn nút "Xác nhận" trong modal
    $("#confirmAction").on("click", function () {
        if (currentForm) {
            currentForm.submit(); // Gửi form đã lưu
        }
    });
});


$(document).ready(function () {
    // Chọn tất cả các nút có ID bắt đầu bằng "rental-button-"
    const rentalButtons = $('[id^="directPaymentButton-"]');
    let currentForm = null; // Biến lưu form hiện tại

    rentalButtons.on("click", function (event) {
        event.preventDefault(); // Ngăn không gửi form ngay lập tức
        currentForm = $(this).closest('form'); // Lưu form hiện tại
        $("#confirmationModal").modal('show'); // Hiển thị modal
    });

    // Xử lý khi nhấn nút "Xác nhận" trong modal
    $("#confirmAction").on("click", function () {
        if (currentForm) {
            currentForm.submit(); // Gửi form đã lưu
        }
    });
});
