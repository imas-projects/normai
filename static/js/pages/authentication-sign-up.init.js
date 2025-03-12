
// Código propio para coger el formulario de Creación de Usuario
document.getElementById('sign-up-form').addEventListener('submit', function (event) {
    console.log('editform submitted!'); //debug
    event.preventDefault();
    const data = {
            username: document.getElementById('username').value,
            useremail: document.getElementById('useremail').value,
            password: document.getElementById('password-input').value,            
    };
    
    fetch('/authentication/sign-up/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),    
    })  
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Row updated successfully!');
                location.reload();
            } else {
                alert('Failed to update row.');
            }
        });
    });
