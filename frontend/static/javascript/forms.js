function inputTouched(input) {
    if (input.value == "" || input.value == null) {
        input.classList.remove("touched");
    } else {
        input.classList.add("touched");
    }
}

function removeTouched(input) {
    input.classList.remove("touched");
}


function websiteField(input) {
    var ex = /[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/;
    var regex = new RegExp(ex);
    if (input.value.match(regex)) {
        input.setCustomValidity("");
    } else {
        input.setCustomValidity("Please enter a valid webaddress.");
    }

    $("websiteInput:last-of-type").focus();
}

function parseCategoryList(data) {
    data.sort(function (a, b) {
        return (a[0] < b[0] ? -1 : (a[0] > b[0] ? 1 : 0));
    });
    result = {}
    for (category of data) {
        c = category[1].split(".");
        if (c.length == 1) {
            result[c[0].toLowerCase()] = category;
        } else {
            result[c[0].toLowerCase()][c[1].toLowerCase()] = category;
        }
    }
    return result;
}


$(document).ready(function () {
    $("#signupForm").on("blur", "input[name=website]", function () {
        if ($(this).is(":last-of-type") && !(this.value == "" || this.value == null)) {
            input = $("<input id='websiteInput' type='text' name='website' placeholder='Your website..' onblur='inputTouched(this);'onfocus='removeTouched(this)' required size='1024'>");
            $(this).after(input);
            input.focus();
        } else if (!$(this).is(":last-of-type") && (this.value == '' || this.value == null)) {
            $(this).remove();
        }
        inputlist = $("input[name=website]");
        inputlist.prop("required", true);
        if (inputlist.length > 1) {
            inputlist.last().prop("required", false);
        }
    });

    var intinput = $("#interestsInput")
    if (intinput.length) {
        autoComplete(intinput);
        if (typeof usercategories !== 'undefined') {
            for (let i = 0; i < usercategories.length; i++) {
                intinput.submit(usercategories[i][1].toLowerCase().split("."));
            }
        }
        intinput.sl.hide();
    }

});

