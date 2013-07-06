<?PHP

	$url = "http://www.biomedcentral.com/oai/2.0/?verb=ListRecords&metadataPrefix=oai_dc";
	
	$hostlist = array();
	
	function make_article_record($host, $identifier, $title, $date, $subject, $description){
	
		if(!file_exists(getcwd() . "/hostdata/" . $host)){
		
			mkdir(getcwd() . "/hostdata/" . $host);
		
		}
	
		if(!file_exists(getcwd() . "/hostdata/" . $host . "/" . urlencode($identifier))){

			mkdir(getcwd() . "/hostdata/" . $host . "/" . urlencode($identifier));

		}
	
		file_put_contents(getcwd() . "/hostdata/" . $host . "/" . urlencode($identifier) . "/title.txt", $title);
		file_put_contents(getcwd() . "/hostdata/" . $host . "/" . urlencode($identifier) . "/date.txt", $date);
		file_put_contents(getcwd() . "/hostdata/" . $host . "/" . urlencode($identifier) . "/subject.txt", $subject);
		file_put_contents(getcwd() . "/hostdata/" . $host . "/" . urlencode($identifier) . "/description.txt", $description);		
	
	}
	
	function make_author_record($author, $identifier){
	
		if(!file_exists(getcwd() . "/authordata/" . urlencode($author))){

			mkdir(getcwd() . "/authordata/" . urlencode($author));

		}
		
		file_put_contents(getcwd() . "/authordata/" . urlencode($author) . "/" . urlencode($identifier), "");
	
	}
	
    function get_url($url){

		global $hostlist;

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

		$xml = simplexml_load_string($data);

		$host = explode("/", $url);
		
		foreach($xml->ListRecords->record as $entry){
			
			$data = $entry->metadata->children("http://www.openarchives.org/OAI/2.0/oai_dc/");
			$elements = $data->children("http://purl.org/dc/elements/1.1/");

			$inner_host = explode("/", $elements->identifier);
			
			if(isset($hostlist[$inner_host[2]])){
			
				$hostlist[$inner_host[2]]++;
			
			}else{
			
				$hostlist[$inner_host[2]]=1;
				
			}
			
			if($inner_host[2]=="www.biomedcentral.com"){
			
				echo $elements->identifier . "<br />";
			
			}
			
			if(!file_exists(getcwd() . "/scrapedata/" . $inner_host[2])){
		
				mkdir(getcwd() . "/scrapedata/" . $inner_host[2]);
		
			}

			make_article_record($host[2], $elements->identifier, $elements->title, $elements->date, $elements->subject, $elements->description);
			
			foreach($elements->creator as $author){
			
				make_author_record($author, $elements->identifier);
				
			}
				
		}

/*		if(isset($xml->ListRecords->resumptionToken[0])){

			$url = str_replace("&metadataPrefix=oai_dc","", $url) . "&resumptionToken=" $xml->ListRecords->resumptionToken[0];
			get_url($url);

		}*/

    }
   
    get_url($url);
	
	echo "<pre>";
	
	print_r($hostlist);
