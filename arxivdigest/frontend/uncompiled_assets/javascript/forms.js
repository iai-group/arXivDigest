function inputTouched(input) {
    if (input.value === "" || input.value === null) {
        input.classList.remove("touched");
    } else {
        input.classList.add("touched");
    }
}

function removeTouched(input) {
    input.classList.remove("touched");
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

    let websiteInputs = [
        {"id": "#dblpInput", "prefix": "dblp.org/"},
        {"id": "#google_scholarInput", "prefix": "scholar.google.com/"},
        {"id": "#semantic_scholarInput", "prefix": "semanticscholar.org/author/"},
    ];

    for (const websiteInput of websiteInputs) {
        const input = $(websiteInput["id"]);
        input.on("blur focus", function () {
            let text = input.val();
            if (!text.length) {
                input.get(0).nextElementSibling.textContent = "";
                input.get(0).setCustomValidity("")
            } else if (text.startsWith(websiteInput["prefix"])) {
                input.get(0).nextElementSibling.textContent = "";
                input.get(0).setCustomValidity("")
            } else {
                let msg = "Address must start with: " + websiteInput["prefix"];
                input.get(0).nextElementSibling.textContent = msg;
                input.get(0).setCustomValidity(msg)
            }
        });
    }


});



