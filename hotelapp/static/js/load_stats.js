$(document).ready(function () {
    // Lấy dữ liệu JSON từ các thẻ script
    const stats = JSON.parse(document.getElementById('stats-data').textContent || '[]');
    const monthStats = JSON.parse(document.getElementById('month-stats-data').textContent || '[]');

    // Khởi tạo biểu đồ ban đầu
    const ctx1 = document.getElementById('roomChartId');
    const ctx2 = document.getElementById('roomMonthChartId');

    ctx1.chartInstance = initializeChart(ctx1, stats, 'bar', 'Thống kê doanh thu theo loại phòng');
    ctx2.chartInstance = initializeChart(ctx2, monthStats, 'line', 'Thống kê doanh thu theo tháng');

    // Hàm khởi tạo biểu đồ
    function initializeChart(canvas, parsedData, chartType, chartLabel) {
        try {
            const labels = parsedData.map(item => item[0]); // Nhãn (loại phòng hoặc tháng)
            const data = parsedData.map(item => item[1]); // Doanh thu

            return new Chart(canvas.getContext('2d'), {
                type: chartType,
                data: {
                    labels: labels,
                    datasets: [{
                        label: chartLabel,
                        data: data,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        } catch (error) {
            console.error('Error initializing chart:', error);
        }
    }
});

// Xử lý cập nhật dữ liệu qua AJAX
$(document).on('submit', 'form', function (event) {
    event.preventDefault();

    const form = $(this);
    const url = form.attr('action') || window.location.href;
    const data = form.serialize();
    const canvas = form.next('canvas')[0]; // Lấy thẻ canvas kế tiếp

    $.ajax({
        url: url,
        method: 'GET',
        data: data,
        success: function (response) {
            // Hủy biểu đồ cũ (nếu có)
            if (canvas.chartInstance) {
                canvas.chartInstance.destroy();
            }

            // Tạo biểu đồ mới với dữ liệu phản hồi
            canvas.chartInstance = new Chart(canvas.getContext('2d'), {
                type: 'line', // Kiểu biểu đồ
                data: {
                    labels: response.labels, // Nhãn từ phản hồi
                    datasets: [{
                        label: 'Thống kê doanh thu',
                        data: response.data, // Dữ liệu từ phản hồi
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        },
        error: function (xhr) {
            console.error('Error in AJAX request:', xhr.responseText);
        }
    });
});
