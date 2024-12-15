function addToCart(roomId,checkindate,checkoutdate, button)
{
    // Gửi yêu cầu đến server để thêm phòng vào giỏ hàng
        fetch('/api/add-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}' // Nếu cần CSRF token
            },
            body: JSON.stringify({
                room_id: roomId,
                checkin_date:checkindate,
                checkout_date:checkoutdate,
                action: 'add'
            })
        })
        .then(response =>{
            return response.json()})
        .then(data => {
            if (data.error) {
                alert(data.error); // Hiển thị lỗi nếu phòng đã có trong giỏ hàng
            } else {
                alert(data.message); // Hiển thị thông báo thành công
                button.classList.add('btn-success'); // Thay đổi giao diện nút
                button.innerHTML = 'Đã chọn'; // Cập nhật nội dung nút
                button.setAttribute('onclick', `removeFromCart(${roomId}, '${checkindate}', '${checkoutdate}', this)`);
            }
        })
        .catch(error => console.error('Error:', error));
}

function removeFromCart(roomId,checkindate,checkoutdate, button) {
        // Gửi yêu cầu đến server để xóa phòng khỏi giỏ hàng
        fetch('/api/add-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}' // Nếu cần CSRF token
            },
            body: JSON.stringify({
                room_id: roomId,
                checkin_date:checkindate,
                checkout_date:checkoutdate,
                action: 'remove'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error); // Hiển thị lỗi
            } else {
                alert(data.message); // Hiển thị thông báo thành công
                button.classList.remove('btn-success'); // Đổi lại giao diện nút
                button.classList.add('btn-primary');
                button.innerHTML = 'Chọn phòng'; // Cập nhật nội dung nút
                button.setAttribute('onclick', `addToCart(${roomId}, '${checkindate}', '${checkoutdate}', this)`);
            }
        })
        .catch(error => console.error('Error:', error));
}
function clearSession(event) {
            event.preventDefault();  // Ngăn việc chuyển trang ngay lập tức

            fetch('/api/clear-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);  // Hiển thị thông báo
                // Chuyển hướng đến URL "Trở lại"
                window.location.href = event.target.href;
            })
            .catch(error => console.error('Error:', error));
}
