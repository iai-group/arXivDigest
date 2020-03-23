$(document).ready(function () {
    $(".articleDescription").each(function () {
        var description = $(this);
        if (description.text().length > 450) {
            var showMore = $("<p class='showMore'>Show more</p>")
            showMore.on("click", function () {
                if ($(this).text() === "Show more") {
                    $(this).text("Show less");
                    description.animate({height: description.get(0).scrollHeight});
                } else {
                    $(this).text("Show more");
                    description.animate({height: "4.6em"});
                }
            });
            description.after(showMore);
        } else {
            description.height("auto")
        }
    });

    $(".saveButton").each(function () {
        $(this).on("click", function () {
            var button = $(this);
            var isSaved = button.hasClass("Saved")
            $.getJSON("/save/" + button.data("value") + "/" + !isSaved, {},
                function (data) {
                    if (data.result === "Success") {
                        button.toggleClass("Saved", !isSaved);
                        if (isSaved) {
                            button.attr("title", "Save this article");
                        } else {
                            button.attr("title", "Remove this article");
                        }
                    }
                });
        })
    });
});
