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


// Add autocomplete to topic input
$(document).ready(function () {

    async function suggest_topics_from_text(text) {
        if (text.length < 1) {
            return {"suggestions": []}
        }
        let result = await $.ajax({
            url: "topics/search/" + encodeURIComponent(text),
            async: false

        }).done(function (data) {
            input.parent().parent().next("form_error").text('');
        }).fail(function () {
            input.parent().parent().next("form_error").text('Topic search request failed.');
        });
        return {"suggestions": result}
    }

    function submit_topics(value) {
        value = value.toLowerCase();
        const hidden_input = $("#hidden_topics_input");
        const interests_list = $("#topic_list");

        if (!input.submitted.some(o => o === value)) {
            if (value.length < 3) {
                input.parent().parent().next().text(
                    "Topics must contain at least 3 characters.");
                input.suggestion_list.hide();
                return false;
            }
            input.parent().parent().next("form_error").text("");
            input.submitted.push(value);
            const li = create_removable_list_element(value, value, input, hidden_input);
            interests_list.append(li);
            hidden_input.val(input.submitted.join("\n"));
            return true;
        }
    }

    const input = $("#topic_input");
    if (input.length) {
        input.submitted = [];
        autoComplete(input, $("#add_topic"), suggest_topics_from_text, submit_topics);
        if (typeof user_topics !== 'undefined') {
            for (const topic of user_topics) {
                input.submit(topic['topic'].toLowerCase());
            }
        }
    }
});


// Add autocomplete to category input
$(document).ready(function () {

    async function suggest_categories_from_text(text) {
        const input_list = text.toLowerCase().split(".");
        const is_sub = input.categories.hasOwnProperty(input_list[0].toLowerCase());
        if (is_sub && input_list.length === 1) {
            input_list.push("")
        }

        let title;
        const suggestions = [];

        if (input_list.length > 2) {
            return {"title": "", "suggestions": []}
        } else if (input_list.length === 2) {
            title = suggestions.length ? "<b> Subcategories:</b>" : "";
            const subcategories = input.sub_categories[input_list[0]];
            for (const subcategory in subcategories) {
                const subcategory_data = subcategories[subcategory];
                if (subcategory_data[1].toLowerCase().includes(input_list[1])) {
                    if (input.submitted.includes(subcategory_data[0])) {
                        continue
                    }
                    suggestions.push(subcategory_data[1].split(".").slice(-1)[0]);
                }
            }
        } else {
            title = "";
            for (const category in input.categories) {
                const category_data = input.categories[category];
                if (category_data[1].toLowerCase().includes(input_list[0])) {
                    suggestions.push(category_data[1]);
                }
            }
        }
        return {
            "title": title,
            "suggestions": suggestions,
        };
    }

    function submit_categories(input_value) {
        input_value = input_value.toLowerCase().split(".");
        const hidden_input = $("#categoriesInput");
        const interests_list = $("#interestsList");

        let category;
        if (input_value.length === 1 && input.categories[input_value[0]]) {
            category = input.categories[input_value[0]]
        } else if (input_value.length === 2 && input.sub_categories[input_value[0]][input_value[1]]) {
            category = input.sub_categories[input_value[0]][input_value[1]]
        }
        if (category && !input.submitted.some(o => o === category[0])) {
            input.submitted.push(category[0]);
            const li = create_removable_list_element(category[1], category[0], input, hidden_input);
            interests_list.append(li);
            hidden_input.val(input.submitted.join(","));
            return true;
        }
    }

    function set_input_value(value) {
        value = value.trim();
        let input_value = input.prev_value.split(".");
        if (input.categories.hasOwnProperty(input_value[0].toLowerCase())) {
            return input_value[0] + "." + value;
        } else
            return value;
    }

    const input = $("#interestsInput");
    if (input.length) {
        const parsed_categories = parseCategoryList(categoryList);
        input.categories = parsed_categories["categories"];
        input.sub_categories = parsed_categories["sub_categories"];
        input.submitted = [];
        autoComplete(input, $("#addCategory"), suggest_categories_from_text,
            submit_categories, set_input_value);
        if (typeof usercategories !== 'undefined') {
            for (let i = 0; i < usercategories.length; i++) {
                input.submit(usercategories[i]['category_name'].toLowerCase());
            }
        }
        input.suggestion_list.hide();
    }

    function parseCategoryList(data) {
        data.sort(function (a, b) {
            return (a[0] < b[0] ? -1 : (a[0] > b[0] ? 1 : 0));
        });

        let categories = {};
        let sub_categories = {};
        for (const category of data) {
            const c = category[1].split(".");
            if (c.length === 1) {
                categories[c[0].toLowerCase()] = category;
                sub_categories[c[0].toLowerCase()] = {};
            } else {
                sub_categories[c[0].toLowerCase()][c[1].toLowerCase()] = category;
            }
        }
        return {"categories": categories, "sub_categories": sub_categories};
    }
});


// Add events to website the website inputs
$(document).ready(function () {

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

function create_removable_list_element(text, data_value, input, hidden_input) {
    let li = $("<li class=\"list-group-item\"></li>");
    li.data("val", data_value);
    let remove_button = $("<span class='glyphicon glyphicon-remove'></span>");
    remove_button.click(function () {
        input.submitted.forEach(function (element, i) {
            if (element === li.data("val")) {
                input.submitted.splice(i, 1);
            }
        });
        hidden_input.val(input.submitted.join(","));
        li.remove();
    });
    li.html("<span class='list_text'>" + text + "</span>");
    li.append(remove_button);
    return li;
}


