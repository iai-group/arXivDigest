$(document).ready(function() {
    const millisInMinute = 60000;
    let lastClosed;
    if (window.localStorage.getItem("s2PopupLastClosed") !== null) {
        lastClosed = new Date(window.localStorage.getItem("s2PopupLastClosed"));
    }

    // Don't show the popup if less than 10 minutes have passed since the last time it was shown.
    if (lastClosed == null || (new Date() - lastClosed) > (10 * millisInMinute)) {
        $("#semantic-scholar-popup").modal("show");
    }

    $("#update-semantic-scholar-form").submit(function (e) {
        e.preventDefault();
        this.submit();
        $("#semantic-scholar-popup").modal("hide");
        setTimeout(function() {
            if (location.pathname.includes("/profile")) {
                location.reload();
            }
        }, 1000);
    });
    
    $("#close-semantic-scholar-popup").click(function(e) {
        e.preventDefault();
        window.localStorage.setItem("s2PopupLastClosed", new Date().toISOString());
       $("#semantic-scholar-popup").modal("hide");
    });
})
