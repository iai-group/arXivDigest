function inputTouched(input) {
    //only if element is not empty
    if (input.value == "" || input.value == null) {
        input.classList.remove("touched");
    } else {
        input.classList.add("touched");
    }
}

function removeTouched(input) {
    input.classList.remove("touched");
}

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
    } return result;
}

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
        // up (38), down (40)
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
        // esc
        else if (e.which == 27) {
            input.sl.hide();
            input.val(input.lastVal)
        }
        // enter (13) , tab (9)
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
            var cat = categories[c][1].split(".");
            if (c.length > 1 && cat[cat.length - 1].toLowerCase() != inputData)
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
var intinput = $("#interestsInput")
if (intinput.length) {
    autoComplete(intinput);
    if (usercategories.length) {
        for (let i = 0; i < usercategories.length; i++) {
            intinput.submit(usercategories[i][1].toLowerCase().split("."));
        }
    }
    intinput.sl.hide();
}

$(document).ready(function () {
    $(".articleDescription").each(function () {
        var description = $(this);
        if (description.text().length > 450) {
            var showMore = $("<p class='showMore'>Show more</p>")
            showMore.on("click", function () {
                if ($(this).text() === "Show more") {
                    $(this).text("Show less");
                    description.animate({ height: description.get(0).scrollHeight });
                } else {
                    $(this).text("Show more");
                    description.animate({ height: "4.6em" });
                };
            })
            description.after(showMore);
        } else {
            description.height("auto")
        }
    })
    $(".likeButton").each(function () {
        $(this).on("click", function () {
            var button = $(this);
            var isLiked = button.hasClass("Liked")
            $.getJSON("/like/" + button.data("value") + "/" + !isLiked, {},
                function (data) {
                    if (data.result == "Success") {
                        button.toggleClass("Liked", !isLiked);
                        if (isLiked) {
                            button.attr("title", "Like this article");
                        } else {
                            button.attr("title", "Unlike this article");
                        }
                    }
                });
        })
    })

    $(".systemList tbody").on("click", ".toggleSystem", function () {
        var box = $(this);
        var isActive = !box.prop("checked")
        $.getJSON("/admin/systems/toggleActive/" + box.data("value") + "/" + !isActive, {},
            function (data) {
                if (data.success == true) {
                    box.prop("title", isActive ? "Activate this system." : "Deactivate this system.");
                    box.data("checked", !isActive)
                }
            });
    })
    $("#submitSystem").on("click", function () {
        var button = $(this);
        if ($("#systemName").val() == "") {
            alert("Name can't be empty.")
            return
        }
        $.getJSON("/admin/systems/add/" + $("#systemName").val(), {},
            function (data) {
                if (data.success == true) {
                    generateSystemTableHtml(data.systems);
                } else if (data.error == "Name too long") {
                    alert("Name must be shorter than 255 characters.");
                } else if (data.error == "Name taken") {
                    alert("Another system already uses this name");
                }
            });
    })
    $("ul.nav a[href ='#systems']").bind("show.bs.tab", function () {
        $.getJSON("/admin/systems/get", {},
            function (data) {
                if (data.success == true) {
                    generateSystemTableHtml(data.systems)
                }
            });
    });
    $("ul.nav a[href ='#general']").bind("show.bs.tab", function () {
        $.getJSON("/admin/general", {},
            function (data) {
                if (data.success == true) {
                    plotcontainer = $("#userPlotContainer");
                    $("#userPlot").remove();
                    plotcontainer.append("<canvas id='userPlot'></canvas>");
                    var ctx = $("#userPlot")[0].getContext('2d');
                    var myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.users.dates,
                            datasets: [{
                                label: 'User registration past month',
                                data: data.users.users,
                                backgroundColor: 'rgba(100, 159, 64, 0.2)'
                            }]
                        },
                    });
                    plotcontainer = $("#articlePlotContainer");
                    $("#articlePlot").remove();
                    plotcontainer.append("<canvas id='articlePlot'></canvas>");
                    var ctx = $("#articlePlot")[0].getContext('2d');
                    var myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.articles.dates,
                            datasets: [{
                                label: 'Articles scraped past month',
                                data: data.articles.articles,
                                backgroundColor: 'rgba(100, 159, 64, 0.2)'
                            }]
                        },
                    });

                    $("#statistics").text("Total users: " + data.users.total + "\n Total articles:" + data.articles.total)
                }

            });
    });

    $(".nav-tabs a").click(function () {
        $(this).tab("show");
    });

    if (location.hash) {
        $("ul.nav a[href='" + location.hash + "']").tab("show");
    } else {
        $(".nav li:first-child a").tab("show");
    }


});

function generateSystemTableHtml(systems) {
    html = "<tr>";
    for (const system of systems) {
        html += "<td>" + system.system_ID + "</td>";
        html += "<td>" + system.system_name + "</td>";
        html += "<td>" + system.api_key + "</td>";
        html += "<td><input class='toggleSystem' type='checkbox' data-value=" + system.system_ID
        if (system.active) {
            html += " checked"
        }
        html += system.active ? " title='Deactivate this system.'" : " title='Activate this system.'"
        html += "></td></tr>";
    }
    $(".systemList tbody").html(html)
}
