function autoComplete(input, submit_button,
                      suggestion_func,
                      submit_func,
                      set_input_value_func = value => value.trim()) {
    submit_button.on("click", function (e) {
        e.preventDefault();
        input.submit();
        input.trigger("blur");
    });
    input.attr("autocomplete", "off");
    input.suggestion_list = $("<div class='autocomplete-suggestions'></div>");
    input.suggestion_list.appendTo(input.parent());
    input.submitted = [];


    input.update_suggestionbox = function (next) {
        if (!next) {
            input.suggestion_list.scrollTop(0);
        } else {
            const sl = input.suggestion_list;
            const selectedTop = next.offset().top - sl.offset().top;
            const height = parseInt(sl.css("height"));
            if (selectedTop + next.outerHeight() >= height) {
                sl.scrollTop(next.outerHeight() + sl.scrollTop() + selectedTop - height)
            } else if (selectedTop < 0) {
                sl.scrollTop(selectedTop + sl.scrollTop())
            }
        }
    };

    input.suggestion_list.on("mouseenter", ".autocomplete-suggestion", function () {
        $(".autocomplete-suggestion.selected", input.suggestion_list).removeClass("selected");
        $(this).addClass("selected");
    });

    input.suggestion_list.on("mousedown click", ".autocomplete-suggestion", function (e) {
        const item = $(this);
        const val = item.text();
        if (val && item.hasClass("autocomplete-suggestion")) {
            onSelect(val);
        }
        input.shouldfocus = true;
    });

    input.on("blur", function () {
        input.suggestion_list.hide();
        if (input.shouldfocus) {
            input.focus();
            input.shouldfocus = false;
        }
    });

    input.on("focus", function () {
        input.prev_value = "\n";
        input.trigger("keyup");
        input.suggestion_list.show();
    });

    input.on("keydown", function (e) {
        input.suggestion_list.show();
        if ((e.which === 38 || e.which === 40) && input.suggestion_list.html()) {
            let next_element;
            let selected_element = $(".autocomplete-suggestion.selected", input.suggestion_list);
            if (!selected_element.length) {
                let list = $(".autocomplete-suggestion", input.suggestion_list);
                next_element = (e.which === 40) ? list.first() : list.last();
                next_element.addClass("selected");
                input.val(set_input_value_func((next_element.text())));
            } else {
                if (e.which === 40) {
                    next_element = selected_element.next(".autocomplete-suggestion");
                } else {
                    next_element = selected_element.prev(".autocomplete-suggestion");
                }
                selected_element.removeClass("selected");
                if (next_element.length) {
                    next_element.addClass("selected");
                    input.val(set_input_value_func((next_element.text())));
                } else {
                    input.val(input.prev_value);
                    next_element = 0;
                }
            }
            input.update_suggestionbox(next_element);
            return false;
        } else if (e.which === 27) { // Escape
            input.suggestion_list.hide();
            input.val(input.prev_value)
        } else if (e.which === 13 || e.which === 9) { // Enter or tab
            let selected = $(".autocomplete-suggestion.selected", input.suggestion_list);
            e.preventDefault();
            if (selected.length && input.suggestion_list.is(":visible")) {
                onSelect(selected.text())
            } else {
                input.submit()
            }
        }
    });

    input.on("keyup", function (e) {
        // Enter, escape, end, home, left, up, right, down
        if (![13, 27, 35, 36, 37, 38, 39, 40].includes(e.which)) {
            if (input.val() !== input.prev_value) {
                input.prev_value = input.val();
                input.generateSuggestionList()
            }
        }
    });

    input.generateSuggestionList = function () {
        const input_value = input.val();

        suggestion_func(input_value).then(function (suggestion_data) {
            const choices = suggestion_data["suggestions"];
            const title = suggestion_data["title"] || "";

            if (!choices.length) {
                input.suggestion_list.html("");
                return;
            }

            let search = input_value.split(/[. ,]/g).join(" ");
            search = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
            search = search.split(" ").join("|");
            const re = new RegExp("(" + search + ")", "gi");

            let s = "";
            for (let i = 0; i < choices.length; i++) {
                s += "<div class='autocomplete-suggestion' " +
                    "data-toggle='tooltip' title='" + choices[i] + "' >";
                s += choices[i].replace(re, "<b>$1</b>") + "</div>";
            }
            if (title) {
                s = "<div class='autocomplete-header'>" + title + "</div>" + s;
            }
            input.suggestion_list.html(s);
            input.update_suggestionbox(0);
        });
    };

    function onSelect(value) {
        value = value.trim();
        value = set_input_value_func(value);
        input.val(value);
        input.prev_value = input.val();
        input.suggestion_list.hide();
        input.generateSuggestionList();
    }

    input.submit = function (value) {
        if (!value) {
            value = input.val();
        }
        const submit = submit_func(value);
        if (submit) {
            input.val("");
            input.prev_value = "";
            input.generateSuggestionList();
            input.suggestion_list.hide()
        }
    };

}
