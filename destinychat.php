<?php
$stream = addslashes(strip_tags(trim($_GET['stream'])));
$s = addslashes(strip_tags(strtolower(trim($_GET['s']))));
$t = addslashes(strip_tags(strtolower(trim($_GET['t']))));

//what the fuck, go use destiny's website for this FeedNathan
if(strtolower($stream) == "destiny")
{
  header('Location: http://destiny.gg/bigscreen');
}

//set the default stream time to twitch
if($s == "" && $stream == "")
{
  $s = "strims";
}

//if no time is set start from the beginning
if($t == "")
{
  $t = "0";
}
?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="icon" href="favicon.ico">
    <title>OverRustle - Beta</title>
    <link href="css/bootstrap.min.css" rel="stylesheet">
    <link href="css/overrustle.css" rel="stylesheet">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
    <!-- HTML5 shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
    <script>
      (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

      ga('create', 'UA-49711133-1', 'overrustle.com');
      ga('send', 'pageview');
    </script>    
    <script>
      function twitchAPI() {
        $.ajax({
          url: "https://api.twitch.tv/kraken/streams/<?php echo $stream; ?>?callback=?",
          jsonp: "callback",
          dataType: "jsonp",
          data: {
            format: "json"
          },
         
          success: function(apiData) {
            var output = formatNumber(apiData.stream.viewers) + " Viewers";
            document.getElementById("twitch-ajax").innerHTML = output;
          }
        });
      } 
    </script>
   <script>
    var ws = new WebSocket("ws://overrustle.com:9998/ws");

    var sendObj = new Object();
    sendObj.strim = "/destinychat?s=<?php echo $s ?>&stream=<?php echo $stream; ?>";

    //if we get connected :^)
    ws.onopen = function(){
        console.log('Connected to OverRustle.com Websocket Server :^)');
      sendObj.action = "join";
      ws.send(JSON.stringify(sendObj));
    };

    //if we get disconnected >:(
    ws.onclose = function(evt) {
      console.log('Disconnected from OverRustle.com Websocket Server >:(');
    };

    //the only time we ever get a message back will be a server broadcast
    ws.onmessage = function (evt) {
      document.getElementById("server-broadcast").innerHTML = "" + formatNumber(evt.data) + "";
    };

    //function code for grabbing current viewcount via websocket.
    function overRustleAPI() {
      sendObj.action = "viewerCount";
      ws.send(JSON.stringify(sendObj));
    }

    //update the viewer count every 5 seconds
    window.setInterval(function(){overRustleAPI()}, 5000);

    //On Disconnect 
    $(window).on('beforeunload', function() {
      sendObj.action = "unjoin";
      ws.send(JSON.stringify(sendObj));
    });
    </script>
    <?php
    if ($s == "twitch")
    {

      echo '<script>twitchAPI(); window.setInterval(function(){twitchAPI()}, 60000);</script>';
    }
    ?>
  </head>

  <body>

<nav class="navbar navbar-default navbar-inverse" role="navigation">
  <div class="container-fluid">
    <!-- Brand and toggle get grouped for better mobile display -->
    <div class="navbar-header">
      <a class="navbar-brand" href="/strims">OverRustle</a>
    </div>

    <!-- Collect the nav links, forms, and other content for toggling -->
    <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
      <ul class="nav navbar-nav">
        <li><a href="#"><div id="twitch-ajax"></div></a></li>
        <li><a target="_blank" href="/strims"><div id="server-broadcast"></div></a></li>
        <li class="donate"><a target="_blank" href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=6TUMKXJ23YGQG"><span>Donate</span></a></li>
        <li class="dropdown">
          <a href="#" class="dropdown-toggle" data-toggle="dropdown">Advanced<span class="caret"></span></a>
          <ul class="dropdown-menu" role="menu">
            <li><a target="_blank" href="https://github.com/ILiedAboutCake/OverRustle#">Github</a></li>
            <li><a target="_blank" href="http://overrustle.com:9998/api">Streams API</a></li>
            <li class="divider"></li>
            <li><a target="_blank" href="http://destiny.gg">Destiny.gg</a></li>
          </ul>
        </li>
      </ul>
      <ul class="nav navbar-nav navbar-right">
      <form action="destinychat" class="navbar-form navbar-left" role="search">
        <div class="form-group">
          <select name="s" class="form-control">
            <option value="twitch">Twitch</option>
            <option value="twitch-vod">Twitch - VOD</option>
            <option value="hitbox">Hitbox</option>
            <option value="castamp">CastAmp</option>            
            <option value="youtube">Youtube</option>
            <option value="mlg">MLG (Beta*)</option>
            <option value="ustream">Ustream (Beta*)</option>
            <option value="dailymotion">Dailymotion</option>
            <option value="advanced">Advanced</option>
          </select>
          <input type="text" name="stream" type="text" class="form-control" placeholder="Stream/Video ID"/> 
          <button type="submit" class="btn btn-default">Go</button>
        </div>
      </form>

      </ul>
    </div><!-- /.navbar-collapse -->
  </div><!-- /.container-fluid -->
</nav>

    <div class="container-full fill">
      <div class="pull-left stream-box" id="map">
        <iframe width="100%" height="100%" marginheight="0" marginwidth="0" frameborder="0" src="http://www.twitch.tv/followgrubby/embed" scrolling="no"></iframe>
      </div>
      <div class="pull-right" id="map" style="width: 390px;">

      <!-- TODO: support other chat options than twitch -->
      <div>
        <ul class="nav nav-pills" role="tablist" style="
            position: absolute;
            width: 100%;
            background: #222;
        ">
          <li class="active"><a href="#destinychat" role="tab" data-toggle="tab">Destiny Chat</a></li>
          <li><a href="#otherchat" role="tab" data-toggle="tab"><?php $s; ?> Chat</a></li>
        </ul>
      </div>

      <div class="tab-content" style="height: 100%;">
        <div class="tab-pane fade active in" id="destinychat" style="height: 100%;">
          <iframe width="100%" marginheight="0" marginwidth="0" frameborder="0" src="http://destiny.gg/embed/chat" scrolling="no" style="height: 100%;"></iframe>
        </div>
        <div class="tab-pane fade" id="otherchat" style="height: 100%;">
        <?php
        if ($s == "twitch")
        {
          echo '<iframe width="100%" height="100%" marginheight="0" marginwidth="0" frameborder="0" src="http://www.twitch.tv/' . $stream . '/chat?popout=" scrolling="no"></iframe>';
        }
        else
        {
          echo '<h2>' . $s . ' chat is unsupported</h2>';
        }
        ?>
        </div>
      </div>
    </div>
  </div>
  <script src="js/bootstrap.min.js"></script>
  <!-- Nav tabs -->
  <script src="//cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.1.1/js/tab.min.js"></script>
  <script src="js/overrustle.js"></script>
  </body>
</html>
