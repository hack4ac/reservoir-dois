<?PHP

	function get_biomedcentral_page($url, $host){
		
		$useragent="Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.1) Gecko/20061204 Firefox/2.0.0.1";

		$ch = curl_init();

		curl_setopt($ch, CURLOPT_USERAGENT, $useragent);
		curl_setopt($ch, CURLOPT_URL, $url);
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 
		curl_setopt($ch, CURLOPT_HEADER, 0); 
		curl_setopt($ch, CURLOPT_VERBOSE, true);
		curl_setopt($ch, CURLOPT_PORT , 80);
		curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 100); 
		curl_setopt($ch, CURLOPT_TIMEOUT, 100); 
		curl_setopt($ch, CURLOPT_MAXREDIRS, 10); 
		$data = curl_exec($ch);

		$sections = explode("<section>",$data);
		
		array_shift($sections);
		
		$save = false;
		
		foreach($sections as $section){
		
			if(strpos($section, "<h3>Data and methods</h3>")!==FALSE){
		
				file_put_contents(getcwd() . "/hostdata/" . $host . "/" . urlencode($url) . "/methods.txt", strip_tags($section));
				
				$save = true;
			
			}
			
			if(strpos($section, "<h3>Methods</h3>")!==FALSE){
	
				file_put_contents(getcwd() . "/hostdata/" . $host . "/" . urlencode($url) . "/methods.txt", strip_tags($section));
				
				$save = true;
			
			}
		
		}
	
	}