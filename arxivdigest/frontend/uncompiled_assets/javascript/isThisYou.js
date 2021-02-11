$(document).ready(function() {
    if (window.localStorage.getItem("doNotAskAgain") !== "true") {
        $("#is-this-you").modal("show");
    }
    
    $("#doNotAskAgainCheckbox").change(
    function(){
        if ($(this).is(':checked')) {
            window.localStorage.setItem("doNotAskAgain", "true");
        } else {
            window.localStorage.setItem("doNotAskAgain", "false");
        }
    });

    // Hide the modal and reload the page on form submit.
    $("#update-s2-form").submit(function (e) {
        e.preventDefault();
        this.submit();
        $("#is-this-you").modal("hide");
        setTimeout(function() {
            location.reload();
        }, 1000);
    })
})
