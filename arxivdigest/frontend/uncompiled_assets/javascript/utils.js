function setQueryStringParameter(name, value) {
    const params = new URLSearchParams(window.location.search);
    params.set(name, value);
    let url = `${window.location.pathname}?${params}`;
    if (window.location.hash) {
        url += window.location.hash
    }
    window.history.pushState({}, "", decodeURIComponent(url));
}

function getQueryStringParameter(name, default_value) {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get(name) || !default_value) {
        return urlParams.get(name);
    } else if (default_value) {
        return default_value;
    }
}

function parse_date(date) {
    try {
        date = $.datepicker.parseDate("yy-mm-dd", date);
    } catch (error) {
        date = null;
    }
    return date;
}
