/*fetch('/api/listing/views/')
  .then(response => response.json())
  .then(data => {
      console.log(data)

    });
*/
function chooseDisplayName(name) { 
    switch(name){
        case "views_zillow": 
            return "Zillow";
            break;
        case "views_redfin": 
            return "Redfin";
            break;
        case "views_cb": 
            return "CB";
            break;
        default:
            return name;
    }
}

var myData = "date	Zillow	Redfin	CB\n\
20111001	63	62	72\n\
20111002	58	59	67\n\
20111003	53	59	69\n\
20111004	55	58	68\n\
20111005	64	58	72\n\
20111006	58	57	77\n\
20111007	57	56	82\n\
20111008	61	56	78\n\
20111009	69	56	68\n\
20111010	71	60	68\n\
20111011	67	61	70\n\
20111012	61	61	75\n\
20111013	63	64	76\n\
20111014	66	67	66\n\
20111015	61	64	68\n\
20111016	61	61	70\n\
20111017	62	61	71\n\
20111018	60	59	70\n\
20111019	62	58	61\n\
20111020	65	57	57\n\
20111021	55	56	64\n\
20111022	54	60	72\n";

var margin = {
    top: 20,
    right: 80,
    bottom: 30,
    left: 50
    },
    width = 900 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

var parseDate = d3.time.format("%Y%m%d").parse;

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var color = d3.scale.category10();

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var line = d3.svg.line()
    .interpolate("basis")
    .x(function(d) {
    return x(d.date);
    })
    .y(function(d) {
    return y(d.views);
    });

var svg = d3.select("#container").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var original_data = d3.tsv.parse(myData);
//console.log(original_data)

var data = d3.json('/api/listing/views/', function(data) {
    //console.log(data)
    var out = data.items.map(function(d) {
        //console.log(d.date)
        d.date = d.date.split("T")[0].replaceAll("-", "")
        d.date = parseDate(d.date)
        //console.log(d.date)
        //return d
        return {
            date: d.date, 
            views_zillow: d.views_zillow,
            views_redfin: d.views_redfin,
            views_cb: d.views_cb
        }
    }).sort(function(a, b) { 
        return new Date(b.date) - new Date(a.date);
    })
    
    color.domain(d3.keys(out[0]).filter(function(key) {
        return key !== "date";
    }));

    //console.log(color.domain())

    var sites = color.domain().map(function(name) {
        return {
        name: name,
        values: out.map(function(d) {
            return {
            date: d.date,
            views: +d[name]
            };
        })
        };
    });

    x.domain(d3.extent(out, function(d) {
        return d.date;
    }));
  
    y.domain([
        d3.min(sites, function(c) {
        return d3.min(c.values, function(v) {
            return v.views;
        });
        }),
        d3.max(sites, function(c) {
        return d3.max(c.values, function(v) {
            return v.views;
        });
        })
    ]);

    var legend = svg.selectAll('g')
        .data(sites)
        .enter()
        .append('g')
        .attr("transform","translate(40,40)")
        .attr('class', 'legend');

    legend.append('rect')
        .attr('x', width - 20)
        .attr('y', function(d, i) {
            return i * 20;
        })
        .attr('width', 10)
        .attr('height', 10)
        .style('fill', function(d) {
            return color(d.name);
        });

    legend.append('text')
        .attr('x', width - 8)
        .attr('y', function(d, i) {
            return (i * 20) + 9;
        })
        .text(function(d) {
            return chooseDisplayName(d.name);
        });

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Property views");

    var site = svg.selectAll(".site")
        .data(sites)
        .enter().append("g")
        .attr("class", "site");

    site.append("path")
        .attr("class", "line")
        .attr("d", function(d) {
            return line(d.values);
        })
        .style("stroke", function(d) {
            return color(d.name);
        });
    
    // Add the points

    svg.selectAll("myCircles")
        .data(out)
        .enter()
        .append("circle")
        .attr("fill", "red")
        .attr("stroke", "none")
        .attr("cx", function(d) { return x(d.date) })
        .attr("cy", function(d) { return y(d.views_zillow) })
        .attr("r", 3)

    svg.selectAll("myCircles")
        .data(out)
        .enter()
        .append("circle")
        .attr("fill", "red")
        .attr("stroke", "none")
        .attr("cx", function(d) { return x(d.date) })
        .attr("cy", function(d) { return y(d.views_redfin) })
        .attr("r", 3)

    svg.selectAll("myCircles")
        .data(out)
        .enter()
        .append("circle")
        .attr("fill", "red")
        .attr("stroke", "none")
        .attr("cx", function(d) { return x(d.date) })
        .attr("cy", function(d) { return y(d.views_cb) })
        .attr("r", 3)
 
    site.append("text")
        .datum(function(d) {
            return {
                name: d.name,
                value: d.values[d.values.length - 1]
            };
        })
        .attr("transform", function(d) {
        return "translate(" + x(d.value.date) + "," + y(d.value.views) + ")";
        })
        .attr("x", 3)
        .attr("dy", ".35em")
        .text(function(d) {
            return chooseDisplayName(d.name);
        });

    return out
})








    