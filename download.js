var data = source.data;
var filetext = 'Date, BGT, Broad, Elliot, Fremont, MTS, NW58, Second, Spokane, Thirty, TwoSix\n';
for (i=0; i < data['Fremont'].length; i++) {
    var currRow = [data['Date'][i].toString(),
                  data['BGT'][i].toString(),
                  data['Broad'][i].toString(),
                  data['Elliot'][i].toString(),
                  data['Fremont'][i].toString(),
                  data['MTS'][i].toString(),
                  data['NW58'][i].toString(),
                  data['Second'][i].toString(),
                  data['Spokane'][i].toString(),
                  data['Thirty'][i].toString(),
                  data['TwoSix'][i].toString().concat('\n')
                 ];

    var joined = currRow.join();
    filetext = filetext.concat(joined);
}

var filename = 'data_result.csv';
var blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });

//addresses IE
if (navigator.msSaveBlob) {
    navigator.msSaveBlob(blob, filename);
}

else {
    var link = document.createElement("a");
    link = document.createElement('a')
    link.href = URL.createObjectURL(blob);
    link.download = filename
    link.target = "_blank";
    link.style.visibility = 'hidden';
    link.dispatchEvent(new MouseEvent('click'))
}
