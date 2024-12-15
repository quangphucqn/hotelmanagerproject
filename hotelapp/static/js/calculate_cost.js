document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra xem cart có dữ liệu không
    if (typeof cart !== 'undefined' && cart !== null) {
        // Lặp qua tất cả các phòng trong giỏ hàng và gọi updateRoomPrice cho từng phòng
        Object.keys(cart).forEach(roomId => {
            updateRoomPrice(roomId); // Gọi hàm updateRoomPrice cho từng phòng
        });

        // Gọi updateTotalPrice để tính toán tổng tiền ngay khi trang load
        updateTotalPrice();
    } else {
        console.error("Cart data is not available.");
    }
});

function updateRoomPrice(roomId) {
    const numberPeople = parseInt(document.querySelector(`input[name="number_people_${roomId}"]:checked`)?.value || 2);

    fetch('/api/calculate_room_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            room_id: roomId,
            number_people: numberPeople
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error from server:', data.error);
        } else {
            const roomTotalPrice = data.room_total_price;
            // Cập nhật giá phòng cho phòng tương ứng
            document.getElementById(`price_${roomId}`).innerText = `${roomTotalPrice.toLocaleString()} VNĐ`;
            updateTotalPrice(); // Cập nhật tổng tiền sau khi cập nhật giá phòng
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateTotalPrice() {
    const nationalCoefficient = document.getElementById('national_id').value;

    fetch('/api/calculate_total_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            national_coefficient: nationalCoefficient
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error from server:', data.error);
        } else {
            const totalCost = data.total_cost;
            document.getElementById('total_price').innerText = `Tổng: ${totalCost.toLocaleString()} VNĐ`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
