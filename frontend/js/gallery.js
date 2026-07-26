const gallery =
document.getElementById("gallery");

const uploadButton =
document.getElementById("uploadBtn");

const fileInput =
document.getElementById("fileInput");


loadGallery();


async function loadGallery(){

    const response =
    await fetch(

        API_BASE_URL+"/media/",

        {

            headers:authHeaders()

        }

    );

    const data =
    await response.json();

    gallery.innerHTML="";

    data.forEach(media=>{

        const card =
        document.createElement("div");

        card.className="card";

        if(media.media_type==="image"){

            card.innerHTML=`

            <img src="${API_BASE_URL}/media/${media.id}">

            <p>${media.filename}</p>

            `;

        }

        else{

            card.innerHTML=`

            <video controls>

            <source

            src="${API_BASE_URL}/media/stream/${media.id}">

            </video>

            <p>${media.filename}</p>

            `;

        }

        gallery.appendChild(card);

    });

}


uploadButton.onclick = async ()=>{

    const file =
    fileInput.files[0];

    if(!file){

        alert("Choose a file");

        return;

    }

    const form =
    new FormData();

    form.append("file",file);

    const response =
    await fetch(

        API_BASE_URL+"/media/upload",

        {

            method:"POST",

            headers:{

                Authorization:
                "Bearer "+
                getAccessToken()

            },

            body:form

        }

    );

    if(response.ok){

        alert("Uploaded");

        loadGallery();

    }

    else{

        alert("Upload Failed");

    }

}