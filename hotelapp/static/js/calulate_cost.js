document.addEventListener('DOMContentLoaded', () => {
    const bookingForm = document.getElementById('booking-form');
    const totalCostElement = document.getElementById('total-cost');

    function calculateCost() {
        const roomData = [];
        const nationalId = document.getElementById('national_id').value;

        // Thu thập dữ liệu từ các phòng
        document.querySelectorAll('.number-people:checked').forEach(radio => {
            const roomId = radio.getAttribute('data-room-id');
            const numberPeople = radio.value;
            const checkinDate = document.querySelector(`input[name="checkin-date"]`).value;
            const checkoutDate = document.querySelector(`input[name="checkout-date"]`).value;

            roomData.push({
                room_id: roomId,
                number_people: numberPeople,
                checkin_date: checkinDate,
                checkout_date: checkoutDate
            });
        });

        // Gửi dữ liệu đến server qua AJAX
        fetch('/api/calculate_cost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ room_data: roomData, national_id: nationalId })
        })
            .then(response => response.json())
            .then(data => {
                totalCostElement.textContent = data.total_cost.toLocaleString(); // Cập nhật tổng chi phí
            })
            .catch(error => console.error('Error:', error));
    }

    // Lắng nghe sự kiện thay đổi số người ở
    document.querySelectorAll('.number-people').forEach(radio => {
        radio.addEventListener('change', calculateCost);
    });

    // Lắng nghe sự kiện thay đổi quốc tịch
    document.getElementById('national_id').addEventListener('change', calculateCost);
});