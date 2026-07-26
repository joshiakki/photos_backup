function saveTokens(access, refresh){

    localStorage.setItem(
        "access_token",
        access
    );

    localStorage.setItem(
        "refresh_token",
        refresh
    );

}


function getAccessToken(){

    return localStorage.getItem(
        "access_token"
    );

}


function logout(){

    localStorage.clear();

    window.location="login.html";

}


function authHeaders(){

    return{

        "Authorization":
        "Bearer "+getAccessToken()

    };

}