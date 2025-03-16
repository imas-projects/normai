
// Código propio para coger el formulario de Creación de Usuario

// Envío formulario
document.getElementById('sign-in-form').addEventListener('submit', function (event) {
    console.log('formulario'); //debug
    event.preventDefault();
    const data = {
            username: document.getElementById('username').value,
            password: document.getElementById('password-input').value,          
    };
    console.log(data.password); //debug

    fetch('/authentication/sign-in/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),    
    })  
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del servidor:', data); // debug Ver también la respuesta completa
            if (data.success) {
                //alert('Row updated successfully!');
                window.location.href = data.redirect_url  // Redirección a otra vista
            } else {
                alert('Failed to update row.');
            }
        });
    });
