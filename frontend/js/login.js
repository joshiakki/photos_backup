document
.getElementById("loginForm")
.addEventListener(
"submit",

async function(e){

e.preventDefault();

const email=document.getElementById("email").value;

const password=document.getElementById("password").value;

const response=await fetch(

API_BASE_URL+"/auth/login",

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

const data=await response.json();

if(response.ok){

saveTokens(

data.access_token,

data.refresh_token

);

window.location="gallery.html";

}

else{

alert(data.error);

}

});