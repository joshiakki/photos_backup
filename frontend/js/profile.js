const headers = authHeaders();

loadProfile();


async function loadProfile(){

    const response = await fetch(

        API_BASE_URL + "/users/profile",

        {

            headers

        }

    );

    const data = await response.json();

    document.getElementById("username").value =
        data.username;

}


document
.getElementById("updateProfile")
.onclick = async ()=>{

    const username =
    document.getElementById("username").value;

    const response =
    await fetch(

        API_BASE_URL+"/users/profile",

        {

            method:"PUT",

            headers:{

                ...headers,

                "Content-Type":"application/json"

            },

            body:JSON.stringify({

                username

            })

        }

    );

    if(response.ok){

        alert("Profile Updated");

    }

};


document
.getElementById("changePassword")
.onclick = async ()=>{

    const current_password =
    document.getElementById("currentPassword").value;

    const new_password =
    document.getElementById("newPassword").value;

    const response =
    await fetch(

        API_BASE_URL+"/users/change-password",

        {

            method:"POST",

            headers:{

                ...headers,

                "Content-Type":"application/json"

            },

            body:JSON.stringify({

                current_password,

                new_password

            })

        }

    );

    if(response.ok){

        alert("Password Changed");

    }

    else{

        alert("Failed");

    }

};


document
.getElementById("uploadProfile")
.onclick = async ()=>{

    const file =
    document.getElementById("profileFile").files[0];

    if(!file){

        alert("Choose a file");

        return;

    }

    const form =
    new FormData();

    form.append("file",file);

    const response =
    await fetch(

        API_BASE_URL+"/users/profile-picture",

        {

            method:"POST",

            headers:headers,

            body:form

        }

    );

    if(response.ok){

        alert("Uploaded");

    }

};