#!/usr/bin/env python

import os,sys,re,json,datetime
from glob import glob
from array import array
from optparse import OptionParser,OptionGroup
import warnings

from  pdf_param_cfi import *
from generatePdf_cat import *
from generateFormula import *

warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='.*class stack<RooAbsArg\*,deque<RooAbsArg\*> >' )



basepath=os.path.split(os.path.abspath(__file__))[0]+"/../"
sys.path.append(basepath+"common/")

tempargv = sys.argv[:]
sys.argv = []
import ROOT
from ROOT import *
sys.argv = tempargv

from toolkit import *

colours = ["\033[m"] + ["\033[%d;%dm"%(x,y) for (x,y) in [(0,z) for z in range(31,37)]+[(1,z) for z in range(31,37)]]

gcs=[] # for memory issues
gcs_aux=[] # for memory issues

####################################################################################################
def parser(mp=None):
	if not mp: mp = OptionParser()
#	mp.add_option('','',help=colours[5]+''+colours[0],default='',type='',dest='')
#
#	mg1 = OptionGroup(mp,'GroupTitle')
#	mg1.add_option('','',help=colours[5]+''+colours[0],default='',type='',dest='')
#	mp.add_option_group(mg1)
#
	mp.add_option('--workdir',help=colours[5]+'Case workdir.'+colours[0],default='case0',type='str')
	mp.add_option('--long',help=colours[5]+'Long filenames.'+colours[0],default=False,action='store_true')
	mp.add_option('-v','--verbosity',help=colours[5]+'Verbosity.'+colours[0],default=0,action='count')
	mp.add_option('-q','--quiet',help=colours[5]+'Quiet.'+colours[0],default=True,action='store_false')
#	mp.add_option('-q','--quiet',help=colours[5]+'Quiet.'+colours[0],default=False,action='store_false')
#
	mg1 = OptionGroup(mp,'Selection setup')
	mg1.add_option('--SELCATs',help=colours[5]+'Selection/Category setup.'+colours[0],default='double;DoubleB;-1#0.0875#0.5775#0.7875#1.,single;SingleB;-1#0.0775#0.5775#0.7775#0.8775#1.',type='str',action='callback',callback=SELsetup,dest='SC')# final
	mp.add_option_group(mg1)
#
	mg2 = OptionGroup(mp,'Data template setup')
	mg2.add_option('--bounds',help=colours[5]+'Template boundaries: 80,200 (min,max)'+colours[0],default=[80.,200.],type='str',action='callback',callback=optsplitfloat,dest='X')
	mg2.add_option('--binwidth',help=colours[5]+'Template bin width: 0.1,0.1 (Single,Double)'+colours[0],default=[0.1,0.1],type='str',action='callback',callback=optsplitfloat,dest='dX')
	mg2.add_option('--lumi',help=colours[5]+'Luminosity: 35900(single,double)'+colours[0],default=[35900,35900.],type='str',action='callback',callback=optsplitfloat,dest='LUMI')
	mg2.add_option('--TF',help=colours[5]+'Transfer function label: POL1,POL1 (Single,Double)'+colours[0],default=['POL1','POL1'],type='str',action='callback',callback=optsplit)
	mg2.add_option('--function',help=colours[5]+'Function for bias study :  expPow'+colours[0],default='expPow',type='str')
	mg2.add_option('--forfit',help=colours[5]+'Freeze/free parameters for fit or not (for toys)'+colours[0],default=True,action='store_false')
	mp.add_option_group(mg2)
#
	return mp

####################################################################################################
def style():
	gROOT.SetBatch(1)
	gROOT.ProcessLineSync(".x %s/styleCMSTDR.C"%basepath)
	gROOT.ForceStyle()
	gStyle.SetPadTopMargin(0.06)
	gStyle.SetPadRightMargin(0.04)
	gStyle.SetCanvasBorderMode(0)
	gStyle.SetCanvasColor(0)
	gStyle.SetPadColor(0)
	gStyle.SetPadBorderMode(0)
	gStyle.SetCanvasBorderMode(0)
	gStyle.SetFrameBorderMode(0)
	gROOT.ProcessLineSync("gErrorIgnoreLevel = kWarning;")
	RooMsgService.instance().setSilentMode(kTRUE)
	for i in range(2): RooMsgService.instance().setStreamStatus(i,kFALSE)

def hStyle(h,i,sumw2=True):
	if sumw2: h.Sumw2()
	h.SetMarkerStyle([20,20,23,21,22,24][i])
	h.SetMarkerSize(1.2)
	h.SetMarkerColor([kBlack,kBlue,kRed,kGreen+2,kOrange][i])
	h.SetLineColor([kBlack,kBlue,kRed,kGreen+2,kOrange][i])

def gpStyle(g,i):
	g.SetFillColor([kBlack,kBlue,kRed,kGreen+2,kOrange][i])
	g.SetFillStyle(3004)

def gaStyle(g,i):
	g.SetFillColor(kGray)
	g.SetFillStyle(1001)

####################################################################################################
def RooDraw(opts,can,C,S,x,rh,model,qPDF,zPDF,tPDF,archive,chi2_val,n_param,title):
#	can.cd(C+1)
	can.cd(0)
	can.SetTitle(title)
	can.SetFillColor(0)
	can.SetFillStyle(-1)
#	can.SetLogy()
	print 'plotting'
	gPad.SetBottomMargin(0.3)
	frametop = x.frame()
	framebot = x.frame()
# part 1
	rh.plotOn(frametop)
	model.plotOn(frametop,RooFit.LineWidth(2))
	
#	rhres = frametop.residHist()
	rhres = frametop.pullHist()
	p1 = RooArgSet(qPDF)
	p2 = RooArgSet(zPDF)
	p3 = RooArgSet(tPDF)
	model.plotOn(frametop,RooFit.Components(p1),RooFit.LineWidth(2),RooFit.LineColor(kBlack),RooFit.LineStyle(kDashed))
#	model.plotOn(frametop,RooFit.Components(p2),RooFit.LineWidth(2),RooFit.LineColor(kBlue))
#	model.plotOn(frametop,RooFit.Components(p3),RooFit.LineWidth(2),RooFit.LineColor(kGreen+1))
	frametop.GetXaxis().SetTitleSize(0)
	frametop.GetXaxis().SetLabelSize(0)
	frametop.GetYaxis().SetLabelSize(0.035)
	frametop.GetYaxis().SetTitleSize(0.055)
	frametop.GetYaxis().SetTitleOffset(1.5);
	frametop.GetYaxis().SetTitle("Events / %.1f GeV"%opts.dX[0])
	frametop.Draw()
	gPad.Update()
	
	ndf = int((opts.X[1]-opts.X[0])/opts.dX[0]) - (n_param)
	chi2=chi2_val/ndf
	prob = ROOT.TMath.Prob(chi2_val,ndf)
	print ndf
	print chi2_val
	print prob


# part 2
	pad = TPad("pad","pad",0.,0.,1.,1.)
	pad.SetTopMargin(0.7)
	pad.SetFillStyle(-1)
	pad.SetBorderSize(0)
	pad.Draw()
	pad.cd(0)
	framebot.addPlotable(rhres,"p")
	framebot.GetYaxis().SetTitle("Pulls")
	framebot.GetXaxis().SetTitle("M_{bb} (GeV)")
	framebot.GetYaxis().SetLabelSize(0.03)
	framebot.GetYaxis().SetTitleSize(0.04)
	line = ROOT.TLine(opts.X[0],0,opts.X[1],0)
	line.SetLineStyle(7)
	line.SetLineWidth(2)
	line.SetLineColor(kGreen+2)
	framebot.addObject(line)

	L00 = TLegend(0.7,0.6,1.-gStyle.GetPadRightMargin()-gStyle.GetPadTopMargin()*0.3333,1.-gStyle.GetPadTopMargin()*1.3333)
	L00.SetFillColor(-1)
	L00.SetBorderSize(0)
	L00.SetTextFont(42)
	L00.SetTextSize(gStyle.GetPadTopMargin()*0.60)
	L00.SetY1(L00.GetY2()-L00.GetNRows()*gStyle.GetPadTopMargin()*0.95)
	L00.Draw()
	framebot.addObject(L00)

	pave = TPaveText(0.75,0.7,0.9,0.9,"NDC")
	pave.SetTextAlign(11)
	pave.SetFillStyle(-1)
	pave.SetBorderSize(0)
	pave.SetTextFont(42)
	pave.SetTextSize(gStyle.GetPadTopMargin()*0.60)
	pave.SetTextColor(kBlue+1)
	pave.AddText("%s"%S.label) #.replace('','Set A').replace('PRK','Set B'))
	pave.AddText("%s"%title)
	pave.AddText("#chi^{2}=%.2f"%chi2)
	pave.AddText("Prob=%.2f"%prob)
	pave.Draw()
	framebot.addObject(pave)
	print 'here'

	framebot.Draw()
	gPad.Update()
	archive += [pad]
	archive += [rhres]

####################################################################################################
def main():
# Parse options
	mp = parser()
	opts,args = mp.parse_args()

# Style
	style()

# Create directories if needed
	makeDirs('%s'%opts.workdir)
	makeDirs('%s/plot'%opts.workdir)
	makeDirs('%s/root'%opts.workdir)
	longtag1 = "_%s"%(opts.function)
	
# Setup
	SC = opts.SC if not type(opts.SC)==str else SELsetup(opts.SC)
	fTF = json.loads(filecontent("%s/vbfHbb_transfer_2016_run2_linear.json"%basepath))
	LUMI = opts.LUMI
	NBINS = [int((opts.X[1]-opts.X[0])/x) for x in opts.dX]	
	n_param = Nparam[opts.function] 
	MASS=125

# Files
	fBKG = TFile.Open("%s/root/bkg_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag1),"read")
	fSIG = TFile.Open("%s/root/sig_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag1),"read")
	fTRF = TFile.Open("%s/root/TransferFunctions%s.root"%(opts.workdir,"" if not opts.long else longtag1),"read")
	wBKG = fBKG.Get("w")
	wSIG = fSIG.Get("w")
	w    = RooWorkspace("w","workspace")

# New histograms, graphs, containers
	archive = []
	C0  = TCanvas("c1","c1",900,750)
	rh  = {}
	rhb = {}
	h   = {}
	hb  = {}
	Y   = {}
	
## CMS info
	left,right,top,bottom = gStyle.GetPadLeftMargin(),gStyle.GetPadRightMargin(),gStyle.GetPadTopMargin(),gStyle.GetPadBottomMargin()
	pCMS1 = TPaveText(left,1.-top,0.4,1.,"NDC")
	pCMS1.SetTextFont(62)
	pCMS1.SetTextSize(top*0.75)
	pCMS1.SetTextAlign(12)
	pCMS1.SetFillStyle(-1)
	pCMS1.SetBorderSize(0)
	pCMS1.AddText("CMS")
	pCMS2 = TPaveText(0.5,1.-top,1.-right*0.5,1.,"NDC")
	pCMS2.SetTextFont(42)
	pCMS2.SetTextSize(top*0.75)
	pCMS2.SetTextAlign(32)
	pCMS2.SetFillStyle(-1)
	pCMS2.SetBorderSize(0)
	pCMS2.AddText("L = 35.9 fb^{-1} (13 TeV)")
	c0 = TCanvas("can","can",600,600)

# Selection loop
	for iS,S in enumerate(SC.selections):
## Load tree
		fin = TFile.Open("/afs/cern.ch/work/n/nchernya/VBFHbb_2016/VBF_combine/inputs/root/FitVBF_BTagCSV_analysis_%s_trignone_v25_VBF_newReg.root"%(str.lower(S.tag)),"read")
		T = fin.Get("VBF/events")
## Containers
		brn          = {}
		params   = {}
		qcd_pdf      = {}
		qcd_pdf_aux  = {}
		qcd_pdf_aux2 = {}
		model        = {}
		nQCD         = {}
		transfer     = {}
		zPDF,tPDF,qPDF,sPDF = {},{},{},{}
		yZ,yT,yQ     =  {} ,{},{}
		can = TCanvas("canD_sel%s"%S.tag,"%s"%opts.function,600,600)
#		can.Divide(2,2)
## Category loop
		for C in range(S.ncat):
#######################################
### If you want to only make the plots of the bkg model for the lowest BDT categories, you can comment out the above loop and just put C=0
#		if (1>0):  ##
#			C=0
######################################
			Cp = C + sum([x for x in SC.ncats[0:iS]])
			print C,Cp
####################################################################################################
#### Start of RooFit part 

		#	for ib in range(opts.BRN[iS]+1):
	#			if C>0: continue
#				nb = "b%d_CAT%d"%(ib,Cp)
#				brn[nb] = RooRealVar(nb,nb,0.5,0,10.)
#				nbp = "CAT%d"%(Cp)
#				if not nbp in brn_params: brn_params[nbp] = RooArgList()
#				brn_params[nbp].add(brn[nb])
  ## x
  			x = RooRealVar("mbbReg_CAT%d"%Cp,"mbbReg_CAT%d"%Cp,opts.X[0],opts.X[1])
			x_name="mbbReg_CAT%d"%Cp
			trans_p = {}
  ## Transfer functions			
			if not C==0:
				ftf = fTRF.Get("fRat_sel%s_CAT%d"%(S.label,Cp))
				npar = ftf.GetNpar()
  ### TF Parameters
				ntf = "trans_%s_CAT%d"%(opts.TF[iS],Cp)
				for ip in range(npar):
					if not ntf in trans_p: trans_p[ntf] = []
					trans_p[ntf] += [RooRealVar(ntf+"_p%d"%ip,ntf+"_p%d"%ip,ftf.GetParameter(ip),-0.1,0.1)]
					if 'Fix' in opts.TF[iS]:
						trans_p[ntf][-1].setError(fTF[opts.TF[iS]]['scale'][Cp]*ftf.GetParError(ip))
					else:
						trans_p[ntf][-1].setError(ftf.GetParError(ip))
					trans_p[ntf][-1].setConstant(kTRUE)
  ### TF Functions
				rl = RooArgList(x)
				for ti,t in enumerate(trans_p[ntf]): 
					if ti==0 and fTF[opts.TF[iS]]['f'][-3:]=="+ 1": continue
					rl.add(t)
				ntf = "transfer_%s_CAT%d"%(opts.TF[iS],Cp)
  				transfer[ntf] = RooGenericPdf(ntf,fTF[opts.TF[iS]]['f'],rl)


  ### QCD part
	  ### Containers
			N = "CAT%d"%(Cp)
			h[N]   = TH1F("hMbb_%s"%N,"hMbb_%s"%N,NBINS[iS],opts.X[0],opts.X[1])
			hb[N]  = TH1F("hMbb_blind_%s"%N,"hMbb_blind_%s"%N,NBINS[iS],opts.X[0],opts.X[1])
	  ### Define cut
			cut    = TCut("(bdt_VBF>%1.4f && bdt_VBF<=%1.4f)"%(S.boundaries[C],S.boundaries[C+1]))
			cutB   = TCut("(bdt_VBF>%1.4f && bdt_VBF<=%1.4f) && mbbRegFSR>100 && mbbRegFSR<150"%(S.boundaries[C],S.boundaries[C+1]))
	  ### Draw
	  		c0.cd()
			T.Draw("mbbRegFSR>>%s"%(h[N].GetName()),cut)
			T.Draw("mbbRegFSR>>%s"%(hb[N].GetName()),cutB)
		#	for i in range(NBINS[iS]):
		#		if h[N].GetBinContent(i+1) ==0 : print i
			#	print h[N].GetBinContent(i+1)
			#	print i
	  ### Yields
			Y[N]   = RooRealVar("yield_data_CAT%d"%Cp,"yield_data_CAT%d"%Cp,h[N].Integral())
	  ### Histograms
			rh[N]  = RooDataHist("data_hist_CAT%d"%Cp,"data_hist_CAT%d"%Cp,RooArgList(x),h[N])
			rhb[N] = RooDataHist("data_hist_blind_CAT%d"%Cp,"data_hist_blind_CAT%d"%Cp,RooArgList(x),hb[N])
  ### Model
			print Cp
			if Cp==0 or Cp==4:
				if Cp==4 :  gcs_aux[:]=[]
				[qcd_pdf[N],params[N]] = generate_pdf(x, pdf_name=opts.function,x_name=x_name,selection=S.tag,gcs=gcs_aux) 
				if qcd_pdf[N] == None : return -1
			else:
			#	for ib in range(opts.BRN[iS]+1):
			#		nb = "b%d_CAT%d"%(ib,sum(SC.ncats[0:iS]))
			#		brn[nb].setConstant(kTRUE)
			#	qcd_pdf_aux[N]  = RooBernstein("qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),"qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),x,brn_params["CAT%d"%(sum(SC.ncats[0:iS]))])
				formula = ''
				params_aux = RooArgList()
				for ib in range(n_param): 
					gcs_aux[ib].setConstant(kTRUE)
					gcs_aux[ib].Print()
				#	gcs_aux[ib].setConstant(kTRUE)
				#	gcs_aux[ib].Print()
					params_aux.add(gcs_aux[ib])
				if (opts.function.find('Pol')==-1) : 
					params_aux.add(x)
					formula=generate_formula(pdf_name=opts.function,x_name=x_name,selection=S.tag)
				if (opts.function.find('Pol')==-1) : qcd_pdf_aux[N] =  ROOT.RooGenericPdf("qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),"",formula,params_aux) 
				else : qcd_pdf_aux[N] = RooBernstein("qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),"qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),x,params_aux)
				qcd_pdf_aux2[N] = RooProdPdf("qcd_model_%s_CAT%d"%(''.join(opts.TF),Cp),"qcd_model_%s_CAT%d"%(''.join(opts.TF),Cp),RooArgList(transfer["transfer_%s_CAT%d"%(opts.TF[iS],Cp)],qcd_pdf_aux[N]))
				qcd_pdf[N]      = qcd_pdf_aux2[N] #RooAbsPdf(qcd_pdf_aux2[N])
				if opts.verbosity>0 and not opts.quiet: qcd_pdf[N].Print()
	
	  ### PDFs
	  		zPDF[N] = wBKG.pdf("Z_model_CAT%d"%Cp)
			tPDF[N] = wBKG.pdf("Top_model_CAT%d"%Cp)
			sPDF[N] = wSIG.pdf("signal_model_mH%d_sel%s_CAT%d"%(MASS,S.tag,Cp))

	  ### Yields
	  		yZ[N]    = wBKG.var("yield_ZJets_CAT%d"%Cp)
	  		yT[N]    = wBKG.var("yield_Top_CAT%d"%Cp)
			yQ[N]    = RooRealVar("yield_QCD_CAT%d"%Cp,"yield_QCD_CAT%d"%Cp,1000,0,1e+10)
			yZ[N].setConstant(kTRUE)
			yT[N].setConstant(kTRUE)
#			ySVBF = wSIG.var("yield_signalVBF_mass%d_CAT%d"%(MASS,Cp))
#			ySGF  = wSIG.var("yield_signalGF_mass%d_CAT%d"%(MASS,Cp))
#			yS    = RooRealVar("yield_signal_mass%d_CAT%d"%(MASS,Cp),"yield_signal_mass%d_CAT%d"%(MASS,Cp),ySVBF.getValV()+ySGF.getValV(),0.,400.)

  ### Combined model
	  	#	model[N] = RooAddPdf("bkg_model_CAT%d"%(Cp),"bkg_model_CAT%d"%(Cp),RooArgList(zPDF[N],tPDF[N],qcd_pdf[N]),RooArgList(yZ[N],yT[N],yQ[N]))
	  		model[N] = RooAddPdf("bkg_model_%s_CAT%d"%(opts.TF[iS],Cp),"bkg_model_%s_CAT%d"%(opts.TF[iS],Cp),RooArgList(zPDF[N],tPDF[N],qcd_pdf[N]),RooArgList(yZ[N],yT[N],yQ[N]))
			
  ### Fit
	  		res   = model[N].fitTo(rh[N],RooFit.Save(),RooFit.Warnings(ROOT.kTRUE))
			for gc in gcs_aux :
				gc.Print()
			if opts.verbosity>0 and not opts.quiet: res.Print()


			chi2 = RooChi2Var("chi2", "chi2", model[N], rh[N])
			chi2_val = chi2.getVal()
  ### Draw
  			RooDraw(opts,can,C,S,x,rh[N],model[N],qcd_pdf[N],zPDF[N],tPDF[N],archive,chi2_val,n_param,opts.function)
		#	can.cd(C+1)
			can.cd(0)
			pCMS1.Draw()
			pCMS2.Draw()

  ### Reset constant settings
	#		for ib in range(opts.BRN[iS]+1):
	#			if C==0:
	#				nb = "b%d_CAT%d"%(ib,Cp)
	#				brn[nb].setConstant(kFALSE if opts.forfit else kTRUE)  ## false for final fit, true if fixed
			for ib in range(n_param): 
				if C==0 :
					gcs_aux[ib].setConstant(kFALSE if opts.forfit else kTRUE)  ## false for final fit, true if fixed)
			if not C==0 :
				ntf = "trans_%s_CAT%d"%(opts.TF[iS],Cp)
				for t in trans_p[ntf]: t.setConstant(kFALSE if opts.forfit else (kFALSE if not 'Fix' in opts.TF[iS] else kTRUE)) ## false for final fit, true if fixed
  ### Saving
			for o in [rh[N],rhb[N],model[N],Y[N]]:
				getattr(w,'import')(o,RooFit.RenameConflictNodes("(1)"))
				if opts.verbosity>0 and not opts.quiet: o.Print()
		
###
###--- end of CAT loop
###
		if opts.verbosity>0 and not opts.quiet: w.Print()

#		makeDirs("%s/plot/biasFunctionsCATS/"%opts.workdir)
#		can.SaveAs("%s/plot/biasFunctionsCATS/%s_%s.pdf"%(opts.workdir,can.GetName(),opts.function))
#		can.SaveAs("%s/plot/biasFunctionsCATS/%s_%s.png"%(opts.workdir,can.GetName(),opts.function))
		makeDirs("%s/plot/biasFunctions/"%opts.workdir)
		can.SaveAs("%s/plot/biasFunctions/%s_%s.pdf"%(opts.workdir,can.GetName(),opts.function))
		can.SaveAs("%s/plot/biasFunctions/%s_%s.png"%(opts.workdir,can.GetName(),opts.function))

	
#
#--- end of SEL loop
#

	makeDirs("%s/root/"%opts.workdir)
#	w.writeToFile("%s/root/biasCATS_shapes_workspace_%s.root"%(opts.workdir,opts.function))
	w.writeToFile("%s/root/bias_shapes_workspace_%s.root"%(opts.workdir,opts.function))
	print "Done."

####################################################################################################
if __name__=='__main__':
	main()
