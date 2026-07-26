const API = "/api";


function getToken(){

    return localStorage.getItem(
        "access_token"
    );

}



function logout(){

    localStorage.removeItem(
        "access_token"
    );

    localStorage.removeItem(
        "refresh_token"
    );


    window.location.href =
        "login.html";

}



/*
-----------------------------------------
Register User
-----------------------------------------
*/

async function register(){


    let username =
        document.getElementById("username").value;


    let email =
        document.getElementById("email").value;


    let password =
        document.getElementById("password").value;



    let response = await fetch(

        `${API}/auth/register`,

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


    let data =
        await response.json();



    document.getElementById(
        "message"
    ).innerHTML = data.message;



    if(response.ok){


        setTimeout(()=>{

            window.location.href =
                "login.html";

        },1500);


    }


}




/*
-----------------------------------------
Login User
-----------------------------------------
*/


async function login(){


    let email =
        document.getElementById("email").value;


    let password =
        document.getElementById("password").value;



    let response = await fetch(

        `${API}/auth/login`,

        {


            method:"POST",


            headers:{

                "Content-Type":"application/json"

            },


            body:JSON.stringify({

                email,

                password

            })


        }

    );



    let data =
        await response.json();



    if(response.ok){


        localStorage.setItem(

            "access_token",

            data.access_token

        );


        localStorage.setItem(

            "refresh_token",

            data.refresh_token

        );


        window.location.href =
            "index.html";


    }

    else{


        document.getElementById(
            "message"
        ).innerHTML =
            data.message;

    }

}





/*
-----------------------------------------
Upload Media
-----------------------------------------
*/


async function upload(){


    let file =

    document.getElementById(
        "file"
    ).files[0];



    if(!file){

        return;

    }



    let formData =
        new FormData();



    formData.append(
        "file",
        file
    );



    let response = await fetch(

        `${API}/media/upload`,

        {


            method:"POST",


            headers:{


                "Authorization":

                "Bearer " + getToken()


            },


            body:formData


        }

    );



    let data =
        await response.json();



    document.getElementById(
        "uploadMessage"
    ).innerHTML =
        data.message;



    loadMedia();

}





/*
-----------------------------------------
Load Gallery
-----------------------------------------
*/


async function loadMedia(){


    let response = await fetch(

        `${API}/media/list`,

        {


            headers:{


                "Authorization":

                "Bearer " + getToken()


            }


        }

    );



    if(!response.ok){

        return;

    }



    let media =
        await response.json();



    let html = "";



    media.forEach(item=>{


        html += `

        <div class="media-card">

            <p>
            ${item.filename}
            </p>

            <p>
            Type:
            ${item.media_type}
            </p>


            <a href="/api/media/download/${item.id}"
            target="_blank">

            Open

            </a>

        </div>

        `;


    });



    document.getElementById(
        "gallery"
    ).innerHTML = html;


}