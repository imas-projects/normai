
// Código propio para coger el formulario de Creación de Usuario

// Validación contraseña       
    var myInput=document.getElementById("password-input"),
        letter=document.getElementById("pass-lower"),
        capital=document.getElementById("pass-upper"),
        number=document.getElementById("pass-number"),
        length=document.getElementById("pass-length");
    
    myInput.onfocus=function(){
        document.getElementById("password-contain").style.display="block"
    };
    
    myInput.onblur=function(){
        document.getElementById("password-contain").style.display="none"
    };
    
    myInput.onkeyup=function(){
        myInput.value.match(/[a-z]/g)?(letter.classList.remove("invalid"),letter.classList.add("valid")):(letter.classList.remove("valid"),letter.classList.add("invalid"));
        myInput.value.match(/[A-Z]/g)?(capital.classList.remove("invalid"),capital.classList.add("valid")):(capital.classList.remove("valid"),capital.classList.add("invalid"));
        myInput.value.match(/[0-9]/g)?(number.classList.remove("invalid"),number.classList.add("valid")):(number.classList.remove("valid"),number.classList.add("invalid"));
        8<=myInput.value.length?(length.classList.remove("invalid"),length.classList.add("valid")):(length.classList.remove("valid"),length.classList.add("invalid"))
    };
        
    console.log('contraseñaok'); //debug

// Envío formulario
document.getElementById('sign-up-form').addEventListener('submit', function (event) {
    console.log('formulario'); //debug
    event.preventDefault();
    const data = {
            username: document.getElementById('username').value,
            firstname: document.getElementById('firstname').value,
            lastname: document.getElementById('lastname').value,
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
            console.log('Respuesta del servidor:', data); // debug Ver también la respuesta completa
            if (data.success) {
                alert('Row updated successfully!');
                location.reload();
            } else {
                alert('Failed to update row.');
            }
        });
    });
