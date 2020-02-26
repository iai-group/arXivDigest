function autoComplete(input) {
    $("#addCategory").on("click", function (e) { e.preventDefault(); input.submit(); input.trigger("blur"); });
    input.attr("autocomplete", "off");
    input.sl = $("<div class='autocomplete-suggestions'></div>");
    input.sl.appendTo("body");
    input.submitted = [];
    input.categories = parseCategoryList(categoryList);
    input.hint = input.parent().children(".formhint")

    input.updatesuggestionbox = function (next) {
        input.sl.css({
            top: input.offset().top + input.outerHeight(),
            left: input.offset().left,
            width: input.outerWidth()
        });
        input.sl.show();
        if (!next) input.sl.scrollTop(0);
        else {
            var sl = input.sl
            var selectedTop = next.offset().top - sl.offset().top;
            var height = parseInt(sl.css("height"))
            if (selectedTop + next.outerHeight() >= height) {
                sl.scrollTop(next.outerHeight() + sl.scrollTop() + selectedTop - height)
            } else if (selectedTop < 0) {
                sl.scrollTop(selectedTop + sl.scrollTop())
            }
        }
    }

    input.sl.on("mouseenter", ".autocomplete-suggestion", function () {
        $(".autocomplete-suggestion.selected").removeClass("selected");
        $(this).addClass("selected");
    });

    input.sl.on("mousedown click", ".autocomplete-suggestion", function (e) {
        var item = $(this)
        var val = item.data("val");
        if (val && item.hasClass("autocomplete-suggestion")) {
            onSelect(val);
        }
        input.shouldfocus = true;
    });

    input.on("blur", function () {
        input.sl.hide();
        if (input.shouldfocus) {
            input.focus();
            input.shouldfocus = false;
        }
        input.hint.hide();
    });

    input.on("focus", function () {
        input.hint.css("display", "block");
        input.lastVal = "\n";
        input.trigger("keyup");

    });

    input.on("keydown", function (e) {
        if ((e.which == 38 || e.which == 40) && input.sl.html()) {
            var next, selected = $(".autocomplete-suggestion.selected", input.sl);
            if (!selected.length) {
                list = $(".autocomplete-suggestion", input.sl)
                next = (e.which == 40) ? list.first() : list.last();
                next.addClass("selected")
                setInputVal(next.data("val"));
            } else {
                next = (e.which == 40) ? selected.next(".autocomplete-suggestion") : selected.prev(".autocomplete-suggestion");
                selected.removeClass("selected");
                if (next.length) {
                    next.addClass("selected")
                    setInputVal(next.data("val"));
                } else {
                    input.val(input.lastVal);
                    next = 0;
                }
            }
            input.updatesuggestionbox(next);
            return false;
        }
        else if (e.which == 27) {
            input.sl.hide();
            input.val(input.lastVal)
        }
        else if (e.which == 13 || e.which == 9) {
            var selected = $(".autocomplete-suggestion.selected");
            e.preventDefault();
            if (selected.length && input.sl.is(":visible")) {
                onSelect(selected.data("val"))
            } else {
                input.submit()
            }
        }

    });

    input.on("keyup", function (e) {
        if (!~$.inArray(e.which, [13, 27, 35, 36, 37, 38, 39, 40])) {
            var val = input.val();
            if (val != input.lastVal) {
                input.lastVal = val;
                input.generateSuggestionList()
            }
        }
    });

    input.generateSuggestionList = function () {
        var inputData = input.val().toLowerCase().split(".");
        var category = inputData[0];
        inputData = inputData[1] || category;
        var categories = input.categories[category] || input.categories;
        if (input.categories[inputData])
            inputData = "";
        var choices = [];
        for (const c in categories) {
            var submitted = false
            var cat = categories[c][1].split(".");
            if (cat.length == 2) {
                for (const element of input.submitted) {
                    if (cat[1] == element[1].split(".")[1]) {
                        submitted = true;
                        break;
                    }
                }
            }

            if (c.length > 1 && cat[cat.length - 1].toLowerCase() != inputData && !submitted)
                choices.push(cat[cat.length - 1]);
        }
        var search = inputData.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
        var re = new RegExp("(" + search.split(" ").join("|") + ")", "gi");
        var s = ""

        for (i = 0; i < choices.length; i++)
            if (~choices[i].toLowerCase().indexOf(inputData))
                s += "<div class='autocomplete-suggestion' data-val='" + choices[i] + "'> " + choices[i].replace(re, "<b>$1</b>") + "</div>";
        if (input.categories[category] && s) s = "<div class='autocomplete-header'> <b> Subcategories:</b></div>" + s;
        input.sl.html(s);
        input.updatesuggestionbox(0);
    }

    function onSelect(value) {
        setInputVal(value);
        input.lastVal = input.val();
        input.sl.hide();
        input.generateSuggestionList()
    }

    function setInputVal(value) {
        var inputval = input.lastVal.split(".")
        if (input.categories.hasOwnProperty(inputval[inputval.length - 1].toLowerCase())) {
            inputval.push(value);
        } else
            inputval[inputval.length - 1] = value;
        value = inputval.join(".");
        input.val(value);
    }

    input.submit = function (value) {
        if (!value) {
            var value = input.val().toLowerCase().split(".");
        }
        var category;
        if (value.length == 1 && input.categories[value[0]]) {
            category = input.categories[value[0]]
        } else if (value.length == 2 && input.categories[value[0]][value[1]]) {
            category = input.categories[value[0]][value[1]]
        }
        if (category && !input.submitted.some(o => o[1] === category[1])) {
            input.submitted.push(category);
            var interestslist = $("#interestsList");
            var li = $("<li></li>");
            var remove = $("<span class='glyphicon glyphicon-remove'></span>")
            remove.click(function () {
                var text = li.text();
                input.submitted.forEach(function (element, i) {
                    if (element[1] === text) {
                        input.submitted.splice(i, 1);
                    }

                });
                generateSubmittedCategoriesInput();
                li.remove();
            })
            li.text(category[1]);
            li.append(remove);
            interestslist.append(li);
            input.val("");
            input.lastVal = "";
            input.generateSuggestionList();
            generateSubmittedCategoriesInput();
        }
    }

    function generateSubmittedCategoriesInput() {
        hiddenInput = $("#categoriesInput");
        hiddenInput.val("")
        input.submitted.forEach(element => {
            hiddenInput.val(hiddenInput.val() + element[0] + ",")
        });
    }
}
