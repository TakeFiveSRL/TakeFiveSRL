import sys
import os
import json
import yaml
import ast
import requests
import hashlib
from time import sleep
from SPARQLWrapper import SPARQLWrapper, JSON


class Sparql:
	address = None
	sp = None
	verbose = None

	def __init__(self,verbose):
		self.verbose = verbose
		self.address = "https://w3id.org/framester/sparql"
		self.sp = SPARQLWrapper(self.address)

	def query(self,query):
		if self.verbose == True:
			print "QUERY:",query
		self.sp.setQuery(query)
		self.sp.setReturnFormat(JSON)
		while True:
			try:
				results = self.sp.query().convert()
				break
			except:
				sleep(5)
		if "results" in results:
			return results["results"]["bindings"]
		return results["boolean"]


class coreNLP:

	results = None
	sentence = ""
	verbose = None

	def __init__(self,sentence,verbose):
		self.sentence = sentence
		self.verbose = verbose

	def __getstate__(self):
		return self.sentence,self.results

	def __setstate__(self,d):
		self.sentence = d[0]
		self.results = d[1]

	def getCase(self,dep):
		case = None
		for el in self.results['dependencies']:
			if el[0]==u'case' and el[1]==dep:
				case = el[2]
				break
		return case

	def getCoreNLPInfo(self):
		params = (
                    ('properties', '{"annotators":"tokenize,ssplit,pos,ner,parse,dcoref","outputFormat":"json"}'),
                )

                s = requests.Session()
                response = requests.post('http://173.21.0.4:9000', params=params, data=self.sentence)

                d = json.loads(response.text)
		tmp = dict()
		tmp[u'words'] = list()
		tmp[u'dependencies'] = list()
		for el in d['sentences']:
			for tok in el['tokens']:
				ls = dict()
				ls[u'Lemma'] = tok['lemma']
				ls[u'CharacterOffsetEnd'] = unicode(str(tok['characterOffsetEnd']))
				ls[u'PartOfSpeech'] = tok['pos']
				ls[u'CharacterOffsetBegin'] = unicode(str(tok['characterOffsetBegin']))
				tmp[u'words'].append([tok['word'],ls])
			gbd = list()
			for dep in el['basic-dependencies']:
				bd = list()
				bd.append(unicode(dep['dep']))
				bd.append(unicode(dep['governorGloss']+'-'+str(dep['governor'])))
				bd.append(unicode(dep['dependentGloss']+'-'+str(dep['dependent'])))
				gbd.append(bd)
			tmp[u'dependencies'] = gbd

		if self.verbose == True:
			print "TMP:",tmp



                self.results = dict()
                self.results['words'] = list()
                self.results['dependencies'] = list()

                for el in tmp['words']:
                        self.results['words'].append((el[0],dict(el[1])))

                for el in tmp['dependencies']:
                        self.results['dependencies'].append(list(el))

	def getCompleteRoleFromDep(self,dep,case,reverse=False):
		if reverse==True and dep=='acl':
			return True,'undergoer'
		if reverse == True:
			return False,None
		if case!=None:
			case_cleaned = case[0:case.index("-")]
		if dep=='nsubj':
			return True,'agent'
		if dep=='iobj':
			return True,'recipient'
		if dep=='dobj':
			return True,'undergoer'
		if dep=='mod':
			return True,'oblique'
		if dep=='nmod':
			return True,'oblique'
		if dep=='nmod'and case!=None and case_cleaned==u'in':
			return True,'oblique'
		if dep=='nmod_prep':
			return True,'oblique'
		if dep=='nsubjpass':
			return True,'undergoer'
		if dep=='advcl':
			return True,'oblique'
		if dep=='nmod:agent':
			return True,'agent'
		if dep=='ccomp':
			return True,'eventuality'
		if dep=='xcomp':
			return True,'eventuality'
		if dep=='acl_prep':
			return True,'eventuality'
		if dep=='advcl_prep':
			return True,'eventuality'
		if dep=='advcl':
			return True,'eventuality'
		if reverse==False and dep=='acl':
			return True,'eventuality'
		if dep=='acl_prep':
			return True,'eventuality'
		if dep=='parataxis':
			return True,'eventuality'
		if dep=='tmod':
			return True,'oblique'
		if dep=='nmod:tmod':
			return True,'oblique'
		if dep=='agent':
			return True,'agent'
		if dep=='vmod':
			return True,'undergoer'

		if dep=='nsubj':
			return False,'not(undergoer),not(recipient),not(oblique)'
		if dep=='iobj':
			return False,'not(undergoer),not(agent),not(oblique)'
		if dep=='dobj':
			return False,'not(agent),not(recipient),not(oblique)'
		if dep=='nmod_prep':
			return False,'not(undergoer),not(recipient),not(agent)'
		return False,None

class Framester:

	results = None
	sentence = ""
	verbose = None
	hash_object = None

	def __init__(self,sentence,verbose):
		self.sentence = sentence
		self.hash_object = hashlib.md5(self.sentence)
		self.verbose = verbose
		

	def getbnSynset(self,word):
		for el in self.results:
			for item in self.results[el]:
				for val in self.results[el][item]:
					if val[0]=='word: '+word:
						bnsynset = val[2][10:]
						bnsynset = bnsynset[bnsynset.rindex("/")+1:]
						return bnsynset

	def getInfoFromAPI(self):
		profiles = ['b', 't']
		self.results = dict()
		for i in range(2):
			try:
    				os.stat("./dataframester")
			except:
    				os.mkdir("./dataframester")
			filename = "./dataframester/"+self.hash_object.hexdigest()+".json"
			if os.path.isfile(filename)==False:	
				command = "curl https://lipn.univ-paris13.fr/framester/en/wfd_json/sentence -d \"data="+self.sentence+":"+profiles[i]+"\" -X PUT > "+filename
				try:
					print command
					os.system(command)
				except:
					print "Unexpected error:", sys.exc_info()[0]
			
			try:
				data = yaml.safe_load(open(filename).read())
			except:
				print "CHECK FRAMESTER ON THAT SENTENCE"
				return -1
			if data==None or (isinstance(data,dict)==False and data.find("Service Unavailable")!=-1):
				print "Framester down!!!",filename
				return
			frame_set = list()

			if bool(data)==False or data=="No results from babelfy.":
				print "no results from babelfy"
			else:
				self.results[i] = data


class SemanticRoleLabel:
		
	verbs = list()
	cn = None
	framester = None
	sparql = None
	verbose = None

	def __init__(self,cn,framester,sparql,verbose):
		self.cn = cn
		self.framester = framester
		self.sparql = sparql
		self.verbose = verbose

	def extractVerbsInfo(self):

		for tokeninfo in self.cn.results['words']:
			#print "DEP:",sentence['dependencies']
			#print "WORDS:",sentence['words']
			if tokeninfo[1]['PartOfSpeech']=="VBD" or tokeninfo[1]['PartOfSpeech']=="VB" or tokeninfo[1]['PartOfSpeech']=="VBG" or tokeninfo[1]['PartOfSpeech']=="VBN" or tokeninfo[1]['PartOfSpeech']=="VBP" or tokeninfo[1]['PartOfSpeech']=="VBZ":
				self.verbs.append(tokeninfo)
		#print "List of Verbs extracted from the sentence: ",self.verbs

	def augmentResultsWithFramester(self):
		# first try with profile 'b' if there are frame information for the verb then it does not try the profile 't'
		
		if self.verbose == True:
			print "QUIa",self.verbs
		for verbinfo in self.verbs:
			if self.verbose == True:
				print "verbinfo:",verbinfo
			strpos = "position: "+verbinfo[1]['CharacterOffsetBegin']+"-"+verbinfo[1]['CharacterOffsetEnd']
			idx = 0
			while idx<2 and len(self.framester.results)==2:
				#print "IDX:",idx
				for el in self.framester.results[idx]['annotations']:
					word = el['word']
					position = "position: "+el['begin']+"-"+el['end']#el1[1]
					print "WORD:",word," verbinfo:",verbinfo[0]," position:",position," strpos:",strpos
					if word==verbinfo[0] and position==strpos:
						print "---------------------------------------"
						ret_frame = ast.literal_eval(el['frames'])
						ret_frame_cleaned = [ela[ela.rindex("/")+1:] for ela in ret_frame]
						ret_bnsynset = el['bnsynset']
						if len(ret_frame)!=0:
							verbinfo[1]['frames'] = ret_frame_cleaned
							verbinfo[1]['bnsynset'] = ret_bnsynset[ret_bnsynset.rindex("/")+1:]
							if idx==0:
								verbinfo[1]['profile'] = 'b'
							if idx==1:
								verbinfo[1]['profile'] = 't'
							idx = 2 #exit
				idx = idx + 1
		if self.verbose == True:
			print "QUIFINE",self.verbs

		#print "RET",self.verbs

	def augmentResultsWithNecessaryOptionalRoles(self,sparql):
		for el in self.verbs:
			for frame in el[1]['frames']:
				query = sparql.prepareQueryRoles(frame,'Necessary')
				result = sparql.query(query)
				necRoles = [ v['roles']['value'][v['roles']['value'].index('#')+1:].replace("\"","") for v in result]

				query = sparql.prepareQueryRoles(frame,'Optional')
				result = sparql.query(query)
				optRoles = [ v['roles']['value'][v['roles']['value'].index('#')+1:].replace("\"","") for v in result]

				if 'necessaryRoles' not in el[1]:
					el[1]['necessaryRoles'] = dict()
				if 'optionalRoles' not in el[1]:
					el[1]['optionalRoles'] = dict()
				el[1]['necessaryRoles'][frame] = necRoles
				el[1]['optionalRoles'][frame] = optRoles


	def fillRolesWithSimpleConstraints(self):
		for verb in self.verbs:
			tmp = list()
			for dep in self.cn.results['dependencies']:
				depcleaned = dep[1][0:dep[1].index("-")]
				dep2cleaned = dep[2][0:dep[2].index("-")]
				verbpos = dict()
				if depcleaned==verb[0]:
					val = dict()
					rflag, r = self.cn.getCompleteRoleFromDep(dep[0],self.cn.getCase(dep[2]),False)
					if r!=None:
						val[dep[0]] = r
						if rflag==True:
							val['found']='ok'
						else:
							val['found']='partial'
					else:
						val['found'] = 'no'
					verbpos['positionverb']='two'
					tmp.append((dep,val,verbpos))
				if dep2cleaned == verb[0]:
					val = dict()
					rflag, r = self.cn.getCompleteRoleFromDep(dep[0],None,True)
					if r!=None:
						val[dep[0]] = r
						if rflag==True:
							val['found']='ok'
						else:
							val['found']='partial'
					else:
						val['found'] = 'no'
					verbpos['positionverb']='three'
					tmp.append((dep,val,verbpos))
			verb[1]['results'] = tmp


class VerbNet:

	verbose = None

        def __init__(self,sparql,cn,verbose):
		self.verbose = verbose
		self.sparql = sparql
		self.cn = cn

	#Q1
 	def checkMonosemic(self,verb):
		query = "PREFIX vnschema: <https://w3id.org/framester/vn/schema/> ASK WHERE { 	?verbsense rdfs:label '"+verb+"' ; a vnschema:VerbSense ."\
			"	filter not exists {?verbsense1 rdfs:label '"+verb+"' ; a vnschema:VerbSense ."\
			"	   FILTER (?verbsense != ?verbsense1)} }"
		print "checkmonosemic...:",query
		result = self.sparql.query(query)
		return result


	def selectVerbSense(self,verb):
		query = "PREFIX vnschema: <https://w3id.org/framester/vn/schema/> SELECT DISTINCT ?verbsense "\
 			"WHERE { "\
			"?verbsense rdfs:label '"+verb+"' ; a vnschema:VerbSense . "\
			"filter not exists {?verbsense1 rdfs:label '"+verb+"' ; a vnschema:VerbSense . "\
	   		" FILTER (?verbsense != ?verbsense1)}} "
		
		if self.verbose == True:
			print "SELECTVERBSENSE:",query
		result = self.sparql.query(query)
		ret = set()
		for el in result:
			ret.add(el['verbsense']['value'])
		return ret
		

	#Q8
	def retrieveFirstVerbnetSense(self,verb):
		query = " PREFIX wn30schema: <https://w3id.org/framester/wn/wn30/schema/> PREFIX vnschema: <https://w3id.org/framester/vn/schema/> SELECT DISTINCT ?verbsense "\
			" WHERE { "\
 			" ?verbsense rdfs:label '"+verb+"' ; a vnschema:VerbSense . "\
 			" ?verbsense skos:closeMatch ?wnsense ."\
 			" ?wnsense wn30schema:tagCount ?freq ."\
 			" FILTER ((datatype(?freq)) = xsd:int)"\
			" } ORDER BY DESC(?freq) LIMIT 1"
		if self.verbose == True:
			print query
		result = self.sparql.query(query)
		ret = set()
		for el in result:
			ret.add(el['verbsense']['value'])
		return ret
		

	#Q2 and Q3
	def selectMostSpecificFrameandMaptoVerbSense(self,verb,frames):
		retres = set()
		strframes1 =""
		for frame in frames:
			strframes1 = strframes1 + " ?sframe1 = frame:"+frame+" ||"
		strframes1 = strframes1[:-2]

		toConsider = set()
		for frame in frames:
			query = "PREFIX fn15schema: <https://w3id.org/framester/framenet/tbox/> PREFIX frame: <https://w3id.org/framester/framenet/abox/frame/>  ASK "\
				"WHERE {"\
				"?sframe1 fn15schema:inheritsFrom+ ?sframe2 ; a fn15schema:Frame . "\
				"?sframe2 a fn15schema:Frame "\
				"filter (?sframe2 = frame:"+frame+") "\
				"filter ("+strframes1+")} "
			#print query
			if self.verbose == True:
				print query

			result = self.sparql.query(query)
			if result==False:
				toConsider.add(frame)

		#print "TOCONSIDER:",toConsider

		if len(toConsider)==0:
			return retres
		strframes = ""
		for res in toConsider:
			strframes = strframes + "?frame = frame:"+res + " || "
		strframes = strframes[:-3]
		query1 = "PREFIX vnschema: <http://www.ontologydesignpatterns.org/ont/vn/vnschema31.owl#> "\
			 " SELECT DISTINCT ?verbsense "\
			 " WHERE { "\
			 " ?verbsense rdfs:label '"+verb+"' ; a vnschema:VerbSense; skos:closeMatch ?frame "\
			 " FILTER ( " + strframes + " ) }"
		if self.verbose == True:
			print query1
		#print "QUERY1:",query1
		result1 = self.sparql.query(query1)
		if len(result1)>0:
			for val in result1:
				retres.add(val['verbsense']['value'])

		return retres


	def selectVerbNetRole(self,srl):

		for el in srl.verbs:
			retret = dict()

			if 'verbsenses' not in el[1]:
				#print "BELLO",el[1]
				continue
			for verbsense in el[1]['verbsenses']:
					query = " PREFIX fschema: <https://w3id.org/framester/schema/> PREFIX vnschema: <http://www.ontologydesignpatterns.org/ont/vn/vnschema31.owl#> "\
						" SELECT DISTINCT ?interfacerole ?verbnetrole "\
						" WHERE { "\
						" ?verbnetrole a vnschema:Argument; vnschema:inVerbSense <"+verbsense+"> . "\
						" OPTIONAL { ?verbnetrole fschema:subsumedUnder+ ?interfacerole . ?interfacerole a fschema:InterfaceRole }}"
					#print "QUERY4:",query
					if self.verbose == True:
						print query
					result = self.sparql.query(query)
					ret = list()
					for res in result:
						ret.append(res)
					
					retret[verbsense] = ret
			if 'intverbnetroles' not in el[1]:
				el[1]['intverbnetroles'] = list()
			el[1]['intverbnetroles'] = retret
					
		return
		

	def checkPreposition(self,verbsense,preposition):
		query = "PREFIX vnschema: <https://w3id.org/framester/vn/schema/#> SELECT DISTINCT ?vnrole "\
			"WHERE { "\
 			"?x a vnschema:SensePrepSelection ; "\
    			"vnschema:hasVerbSense <"+verbsense+"> ; "\
    			"vnschema:hasPreposition <https://w3id.org/framester/vn/vn31/data/prep/"+preposition+"> ; "\
    			"vnschema:hasGenericArgument ?vnrole } "
		if self.verbose == True:
			print query
		#print "QUERY6",query
		result = self.sparql.query(query)

		query = "PREFIX vnschema: <https://w3id.org/framester/vn/schema/> "\
			"PREFIX prep: <https://w3id.org/framester/prep/prepont/> "\
			"PREFIX preptype: <https://w3id.org/framester/prep/preptypes/> "\
			"PREFIX prepword: <https://w3id.org/framester/prep/prepwords/> "\
			"SELECT DISTINCT ?vnrole "\
			"WHERE {"\
			" ?x a prep:PrepSynset ; "\
			"    prep:mprep ?prepword ; "\
			"        prep:containsPrepSense ?y . "\
			"    ?y a prep:PrepSense ; "\
			"    prep:frfe ?fe . "\
			"    ?prepword rdfs:label '"+preposition+"' . "\
			"    ?vnrole skos:closeMatch ?fe . "\
			"    ?vnrole vnschema:inVerbSense <"+verbsense+"> } "

		#print "QUERY7",query
		result1 = self.sparql.query(query)

		query = "PREFIX vnschema: <https://w3id.org/framester/vn/schema/> SELECT DISTINCT ?vnrole WHERE { "\
			" ?vnrole vnschema:inVerbSense <"+verbsense+"> ; "\
 			" fschema:subsumedUnder+ framesterrole:oblique }"
		if self.verbose == True:
			print query
		#print query
		result2 = self.sparql.query(query)


		for el in result1:
			result.append(el)
		for el in result2:
			result.append(el)

		#print "RETRET:",result
		return result

	def getPrep(self,vr):
		if vr[0][0]=='nmod':
			val = vr[0][2]
			for el in self.cn.results['dependencies']:
				if el[0]=='case' and el[1]==val:
					preposition = el[2][:el[2].find("-")]
					return preposition
		return ""

	def checkTopRole(self,arg):
		query = "PREFIX vnschema: <http://www.ontologydesignpatterns.org/ont/vn/vnschema31.owl#> "\
			"SELECT DISTINCT ?toprole "\
			"WHERE { "\
			" <"+arg+"> a vnschema:Argument ; fschema:subsumedUnder+ ?toprole . "\
			"?toprole a fschema:TopRole }"
		if self.verbose == True:
			print query
		#print "QUERY 5:",query
		res = self.sparql.query(query)
		ret = set()
		for el in res:
			toprole = el['toprole']['value']
			toprole = toprole[toprole.find("#")+1:].lower()
			ret.add(toprole)
		return ret


	def checkOblique(self,arg):
		query = "PREFIX vnschema: <https://w3id.org/framester/vn/schema/> PREFIX fschema: <https://w3id.org/framester/schema/> PREFIX framesterrole: <https://w3id.org/framester/data/framesterrole/> SELECT DISTINCT ?vnrole "\
			" WHERE { "\
			" ?vnrole vnschema:inVerbSense <"+arg+"> ; "\
 			" fschema:subsumedUnder+ framesterrole:oblique } "
		
		if self.verbose == True:
			print "QUERY 6 BIS:",query,arg
		res = self.sparql.query(query)
		for el in res:
			ret = el['vnrole']['value']
			ret = ret[ret.rindex("/")+1:ret.rindex(".")].lower()
			if self.verbose == True:
				print "ELRET:",ret
			return ret #return just one
		return ""

	def forEachIntRoleVNArgument(self,srl):
		results = list()
		for verb in srl.verbs:
 			if 'intverbnetroles' not in verb[1]:
				continue
			#print "V:",verb
			for res in verb[1]['results']:
				if res[1]['found']=='no':
					continue
				if self.verbose == True:
					print "RES:",res
				intRoleCorenlp = res[1][res[0][0]]	#interfacerole di Corenlp trovata a priori
				for verbsense in verb[1]['intverbnetroles']:
					if len(verb[1]['intverbnetroles'][verbsense])>0:
						if self.verbose == True:
							print "DENTRO1"
						found = False
						for VNarguments in verb[1]['intverbnetroles'][verbsense]:
							if self.verbose == True:
								print "DENTRO2",VNarguments
							intRole = None	#interfacerole di verbnet trovata con query4
							if u'interfacerole' in VNarguments:
								intRole = VNarguments[u'interfacerole']['value']
								intRolecleaned = intRole[intRole.find("#")+1:].lower()
							VNargument = None #verbnetrole di verbnet trovato con query4
							if u'verbnetrole' in VNarguments:
								VNargument = VNarguments[u'verbnetrole']['value']
								VNargumentcleaned = VNargument[VNargument.rfind("/")+1:VNargument.rfind(".")].lower()

							if intRoleCorenlp==intRolecleaned and (intRoleCorenlp=='agent' or intRoleCorenlp=='undergoer' or intRoleCorenlp=='recipient' or intRoleCorenlp=='eventuality'):
								if self.verbose == True:
									print "DENTRO3"
								results.append((res[0],VNargumentcleaned,verbsense,res[2]['positionverb'],'vn'))
								found = True
								if self.verbose == True:
									print "CICICI:",intRolecleaned,verbsense
								break
							elif intRoleCorenlp==intRolecleaned and intRoleCorenlp=='oblique' and 1==2:
								if self.verbose == True:
									print "DENTRO4"
								preposition = self.getPrep(res)
								r = self.checkPreposition(verbsense,preposition)
								if len(r)>0:
									results.append((res[0],VNargumentcleaned,verbsense,res[2]['positionverb'],'vn'))
									if self.verbose == True:
										print "QUIDIVERSO:",VNargumentcleaned
									found = True
									break
								else:
									VNargumentQ6bis = self.checkOblique(verbsense)
									if VNargumentQ6bis!='':
										results.append((res[0],VNargumentQ6bis,verbsense,res[2]['positionverb'],'vn'))
										if self.verbose == True:
											print "QUIDIVERSO2:",VNargumentQ6bis
							elif (intRoleCorenlp == 'agent' or intRoleCorenlp == 'undergoer') and intRoleCorenlp!=intRolecleaned and 1==2:
								if self.verbose == True:
									print "DENTRO5"
								topRoles = self.checkTopRole(VNargument)
								flag = False
								if self.verbose == True:
									print "QUI:",topRoles
								for topRole in topRoles:
									if topRole == "theme":
										results.append((res[0],VNargumentcleaned,verbsense,res[2]['positionverb'],'vn'))
										found = True
										flag = True
										break
								if flag==True:
									break
								
						if found==False:
							if self.verbose == True:
								print "DENTRO6"
							results.append((res[0],intRoleCorenlp,verbsense,res[2]['positionverb'],'in'))
							#print "LAST ELSE",intRoleCorenlp,verbsense
					
					else:
						results.append((res[0],intRoleCorenlp,verbsense,res[2]['positionverb'],'in'))
						if self.verbose == True:
							print "DENTRO7"
							
		return results
						
				
#	{u'type': u'uri', u'value': u'http://www.ontologydesignpatterns.org/ont/framester/data/framesterrole.ttl#agent'} {u'type': u'uri', u'value': u'http://www.ontologydesignpatterns.org/ont/vn/vn31/data/Agent.eat_39010000'}


class SemanticRole:

	results = None
	verbose = None
	sentence = None
	cn = None
	docid = None
	sentenceid = None

	def setVerbose(self,val):
		self.verbose = val
		
	def getCompound(self,word):
		comp = set()
		for el in self.cn.results['dependencies']:
			if el[0]==u'compound' and el[1]==word:
				comp.add(el[2])
			if el[0]==u'compound' and el[2]==word:
				comp.add(el[1])
			if el[0]==u'amod' and el[1]==word:
				comp.add(el[2])
			if el[0]==u'amod' and el[2]==word:
				comp.add(el[1])
		comp.add(word)
		ret = dict()
		for el in comp:
			items = el.rsplit("-",1)
			ret[int(items[1])]=items[0]
		retstr = ""
		for el in sorted(ret):
			retstr = retstr + ret[el] + " "
		return retstr.strip()

	def __init__(self,sentence):
		self.sentence = sentence

	def compute(self):
		sparql = Sparql(self.verbose)

		#CORENLP
		self.cn = coreNLP(self.sentence,self.verbose)
		self.cn.getCoreNLPInfo()
		if self.verbose:
			print "CORENLP:",self.cn.results


		#FRAMESTER
		framester = Framester(self.sentence,self.verbose)
		ret = framester.getInfoFromAPI()
		if ret==-1:
			return -1
		if self.verbose:
			print "FRAMESTER:",framester.results

		#VERBS AND SIMPLECONSTRAINTS
		srl = SemanticRoleLabel(self.cn,framester,sparql,self.verbose)
		srl.extractVerbsInfo()
		srl.augmentResultsWithFramester()
		srl.fillRolesWithSimpleConstraints()
		if self.verbose:
			print "srlverbs:",srl.verbs

		#SRL AUGMENTED WITH VERBSENSES
		verbsenses = dict()
		vbn = VerbNet(sparql,self.cn,self.verbose)
		for verb in srl.verbs:
			if self.verbose:
				print "------------------VERB:",verb
			if vbn.checkMonosemic(verb[1]['Lemma'])==False:
				#performQ2 e Q3
				if self.verbose == True:
					print "monosemic"
				if 'frames' not in verb[1]:
					#print "non ha frames"
					tmp1 = vbn.retrieveFirstVerbnetSense(verb[1]['Lemma'])
					if len(tmp1)>0:
						verb[1]['verbsenses'] = set()
						verb[1]['verbsenses'] = tmp1
					continue
				frames = verb[1]['frames']
				print "!!!!!!!",frames,"!!!!!!"
				tmp = vbn.selectMostSpecificFrameandMaptoVerbSense(verb[1]['Lemma'],frames)
				print "!!!!!!!",tmp,"!!!!!!"
				if len(tmp)==0 or len(tmp)>1:
					tmp1 = vbn.retrieveFirstVerbnetSense(verb[1]['Lemma'])
					#print "NUOVO RETRIEVE",tmp1
					if len(tmp1)>0:
						verb[1]['verbsenses'] = set()
						verb[1]['verbsenses'] = tmp1
					#print tmp1
				elif len(tmp)==1:
					verb[1]['verbsenses'] = set()
					verb[1]['verbsenses'] = tmp
			else:
				print "non monosemico"
				tmp = vbn.selectVerbSense(verb[1]['Lemma'])
				verb[1]['verbsenses'] = set()
				verb[1]['verbsenses'] = tmp
					
	
		if self.verbose:
			print "VERBSENSE:",srl.verbs

	
		#AUGMENTING VERBS WITH VERBNETROLES
		vbn.selectVerbNetRole(srl)

		#if self.verbose:
		print "srlverbs:",srl.verbs


		#RESULTS OF ASSIGN
		self.results = vbn.forEachIntRoleVNArgument(srl)
		unique = []
		for item in self.results:
    			if item not in unique:
        			unique.append(item)
		self.results = unique


if __name__ == "__main__":

	if(len(sys.argv)<>2):
		print "python client.py sentence"
		sys.exit(1)

	srole = SemanticRole(sys.argv[1])
	srole.setVerbose(False)
	srole.compute()

	for el in srole.results:
		print "verb:",el#[0][1],"role:",el[0][2],"verbnet:",el[1]['verbnetrole']['value'],el
