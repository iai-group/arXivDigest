function create_impression_outcome_plot(container, impressions, outcome, labels) {
    let canvas = $("<canvas></canvas>");
    container.append(canvas);
    let ctx = canvas[0].getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Outcome',
                data: outcome,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                pointBorderColor: 'rgba(50, 50, 200, 0.5)',
                pointBackgroundColor: 'rgba(50, 50, 200, 0.5)',
                borderColor: 'rgba(50, 50, 200, 0.5)',

                yAxisID: 'right-y-axis',
                type: 'line'
            }, {
                label: 'Impressions',
                data: impressions,
                yAxisID: 'left-y-axis',
                backgroundColor: 'rgba(100, 150, 50, 0.4)'
            }]
        },
        options: {
            scales: {
                yAxes: [{
                    id: 'left-y-axis',
                    type: 'linear',
                    position: 'left',
                    scaleLabel: {
                        display: true,
                        labelString: 'Impressions'
                    },

                    ticks: {
                        beginAtZero: true,
                        stepSize: 1
                    }
                }, {
                    id: 'right-y-axis',
                    type: 'linear',
                    position: 'right',
                    scaleLabel: {
                        display: true,
                        labelString: 'Outcome'
                    },
                    ticks: {
                        max: 1,
                        beginAtZero: true,
                    }
                }]
            },
        }
    });
}

function create_win_loss_plot(container, wins, ties, losses, labels) {
    let canvas = $("<canvas></canvas>");
    container.append(canvas);
    let ctx = canvas[0].getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Wins',
                data: wins,
                backgroundColor: 'rgba(100, 150, 50, 0.4)'
            }, {
                label: 'Ties',
                data: ties,
                backgroundColor: 'rgba(255, 255, 50, 0.4)',
            }, {
                label: 'Losses',
                data: losses,
                backgroundColor: 'rgba(255, 100, 50, 0.4)',
            },]
        },
        options: {
            scales: {
                yAxes: [{
                    type: 'linear',
                    ticks: {
                        beginAtZero: true,
                        stepSize: 1
                    }
                }]
            },
        }
    });
}

function create_date_controls(container) {
    let controls = $("<div class='form-inline'></div>");
    let date = new Date();
    date.setDate(date.getDate() - 30);
    create_date_selector(controls, "Start date: ", "start_date", date, true, 'end_date', "form-group");
    create_date_selector(controls, "End date: ", "end_date", new Date(), false, 'start_date', "form-group");

    let spacer = $("<label  >Aggregate by: </label>");
    controls.append(spacer);
    controls.on("change", "input[type=radio]", function () {
        setQueryStringParameter("aggregation", this.value);
        create_system_stats_plots(container)
    });

    setQueryStringParameter("aggregation", getQueryStringParameter("aggregation", "day"));
    let month_button = $("<label class='radio-inline'><input type='radio' name='aggregation' value='month'> Months</label>");
    let week_button = $("<label class='radio-inline'><input type='radio' name='aggregation' value='week'> Weeks</label>");
    let day_button = $("<label class='radio-inline'><input type='radio' name='aggregation' value='day'> Days</label>");
    controls.append(month_button);
    controls.append(week_button);
    controls.append(day_button);

    let selector = "input[value='" + getQueryStringParameter("aggregation") + "']";
    controls.children().children(selector).prop("checked", true);
    container.append(controls);
}

function create_date_selector(controls, text, id, date, is_start, other_date, classes) {
    let div = $("<div class='" + classes + "'></div>");
    controls.append(div);

    let field = $("<label for='" + id + "'>" + text + "<input id='"
        + id + "' name='" + id + "' type='text' size='7'></label>");
    div.append(field);


    let options = {
        dateFormat: "yy-mm-dd",
        maxDate: 0,
        changeMonth: true,
        changeYear: true
    };
    if (is_start) {
        options.maxDate = parse_date(getQueryStringParameter(other_date));
    } else {
        options.minDate = parse_date(getQueryStringParameter(other_date));
    }

    let date_selector = field.children('input');
    date_selector.datepicker(options).on("change", function () {
        setQueryStringParameter(id, this.value);
        create_system_stats_plots(controls.parent())
    });
    date_selector.datepicker("setDate", getQueryStringParameter(id, date));
}

function create_system_stats_plots(plot_area) {
    $.ajax({
        url: "/evaluation/system_statistics/" + getQueryStringParameter('system', 0) + window.location.search,
        type: "GET",
        success: function (data) {
            plot_area.empty();
            create_date_controls(plot_area);
            create_impression_outcome_plot(plot_area, data.impressions, data.outcome, data.labels);
            create_win_loss_plot(plot_area, data.wins, data.ties, data.losses, data.labels);
        }
    });
}

function create_mode_controller(plot_area) {
    setQueryStringParameter("mode", getQueryStringParameter("mode", "article"));
    let mode_selector = $("<div class='btn-group btn-group-justified' role='group' ></div><br>");
    let article_choice = $("<a data-mode='article' class='btn btn-default'>Articles</a>");
    let topic_choice = $("<a data-mode='topic' class='btn btn-default'>Topics</a>");
    mode_selector.append(article_choice);
    mode_selector.append(topic_choice);
    let active = mode_selector.find("[data-mode=" + getQueryStringParameter("mode") + "]");
    active.addClass('active no_hover');
    active.siblings().on("click", change_mode);

    return mode_selector;

    function change_mode() {
        let other_button = mode_selector.find(".active");
        setQueryStringParameter("mode", $(this).data('mode'));
        $(this).off("click");
        $(this).addClass("active no_hover");
        other_button.on("click", change_mode);
        other_button.removeClass("active no_hover");
        create_system_stats_plots(plot_area)
    }

}

function create_system_list(evaluation_area, url) {
    let plot_area = $("<div class='col-md-9'></div>");
    evaluation_area.append(plot_area);

    let system_list_container = $("<div class='col-md-3'></div>");
    evaluation_area.append(system_list_container);

    system_list_container.append(create_mode_controller(plot_area));

    let system_list = $("<div class='list-group'></div>");
    system_list_container.append(system_list);

    system_list.on("click", ".list-group-item", function () {
        $(this).siblings().removeClass("active");
        $(this).addClass('active');
        setQueryStringParameter('system', $(this).data("id"))
        create_system_stats_plots(plot_area)
    });

    $.ajax({
        url: url,
        type: "GET",
        success: function (data) {
            for (const system of data["systems"]) {
                const title = "" + system.system_id + "&nbsp;:&nbsp;" + system.system_name;
                let li = $(`<li class='list-group-item' data-id=${system.system_id} 
                                    data-toggle='tooltip' title='${title}'>${title}</li>`);
                system_list.append(li)
            }
        }
    }).always(function () {
        let system_id = system_list.find("[data-id]").first().data("id");
        setQueryStringParameter("system", getQueryStringParameter("system", system_id));
        let system_selector = `[data-id="${getQueryStringParameter("system")}"]`;
        system_list.find(system_selector).addClass("active");
        create_system_stats_plots(plot_area)
    });
}

$(document).ready(function () {
    let evaluation_area = $("#evaluate_systems");
    if (evaluation_area.length) {
        let plot_area = $("<div class='col-md-9'></div>");
        evaluation_area.empty();
        let system_list = create_system_list(evaluation_area, "/evaluation/systems/");
        evaluation_area.append(system_list);
        evaluation_area.append(plot_area);
    }
});

