function sendData() {
    const data = document.getElementById('data-div').textContent;
    console.log(data);

    fetch('/create_rental_note', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: data })
    })
    .then(response => response.text())
    .then(result => {
        alert(result);
    });
}