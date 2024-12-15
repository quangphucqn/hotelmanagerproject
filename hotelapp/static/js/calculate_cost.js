document.addEventListener('DOMContentLoaded', function() {
    // Gọi updateTotalPrice() để tính tổng tiền
    updateTotalPrice();

    // Lấy danh sách các phòng từ giỏ hàng và gọi updateRoomPrice() cho mỗi phòng
    const roomIds = Object.keys(cart); // Giả sử 'cart' là một đối tượng chứa thông tin các phòng
    roomIds.forEach(roomId => {
        updateRoomPrice(roomId);  // Gọi hàm updateRoomPrice cho từng phòng
    });
});
function updateRoomPrice(roomId) {
    const numberPeople = parseInt(document.querySelector(`input[name="number_people_${roomId}"]:checked`).value);

    // Gửi yêu cầu đến server để tính lại giá phòng
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
            // Cập nhật lại giá phòng sau khi tính toán
            const roomTotalPrice = data.room_total_price;
            document.getElementById(`price_${roomId}`).innerText = `${roomTotalPrice.toLocaleString()} VNĐ`;

            // Cập nhật tổng tiền cho tất cả các phòng
            updateTotalPrice();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateTotalPrice() {
    fetch('/api/calculate_total_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            national_coefficient: document.getElementById('national_id').value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error from server:', data.error);
        } else {
            // Hiển thị tổng tiền mới
            const totalCost = data.total_cost;
            document.getElementById('total_price').innerText = `Tổng: ${totalCost.toLocaleString()} VNĐ`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}