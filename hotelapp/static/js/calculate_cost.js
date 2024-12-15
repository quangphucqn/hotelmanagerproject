function updatePrice(roomId) {
    const roomPrice = parseFloat(document.getElementById(`price_${roomId}`).dataset.roomPrice);
    const numberPeople = document.querySelector(`input[name="number_people_${roomId}"]:checked`).value;
    const nationalCoefficient = parseFloat(document.getElementById('national_id').selectedOptions[0].value);

    fetch('/api/calculate_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            room_price: roomPrice,
            number_people: numberPeople,
            national_coefficient: nationalCoefficient
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById(`price_${roomId}`).innerText = `${data.total_price} VNĐ`;
        updateTotalPrice();
    })
    .catch(error => console.error('Error:', error));
}

function updateAllPrices() {
    const rooms = document.querySelectorAll('.room-price');
    rooms.forEach(room => {
        const roomId = room.id.split('_')[1];
        updatePrice(roomId);
    });
}

function updateTotalPrice() {
    let total = 0;
    const rooms = document.querySelectorAll('.room-price');
    rooms.forEach(room => {
        total += parseFloat(room.innerText.replace(' VNĐ', '').replace(',', ''));
    });
    document.getElementById('total_price').innerText = `Tổng: ${total.toLocaleString()} VNĐ`;
}