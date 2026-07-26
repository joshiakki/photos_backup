document
.getElementById("registerForm")
.addEventListener(
"submit",

async function(e){

    e.preventDefault();

    const username =
    document.getElementById("username").value;

    const email =
    document.getElementById("email").value;

    const password =
    document.getElementById("password").value;

    const response = await fetch(

        API_BASE_URL + "/auth/register",

        {

            method:"POST",

            headers:{

                "Content-Type":"application/json"

            },

            body:JSON.stringify({

                username,
                email,
                password

            })

        }

    );

    const data = await response.json();

    if(response.ok){

        alert("Registration Successful");

        window.location = "login.html";

    }

    else{

        alert(data.error);

    }

});