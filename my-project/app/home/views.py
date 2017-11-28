# app/home/views.py

import json
import collections
import requests
import ast
import json


import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import datasets
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd


from firebase import firebase
from flask import abort, flash, redirect, render_template, url_for, request
from flask_login import current_user, login_required

from . import home
from . forms import IssueForm, QueryForm, SubIssueForm
from .. import db
from ..models import Employee, Issue, SubIssue, Query

#firebaseget = firebase.FirebaseApplication('https://eager-621db.firebaseio.com/Reports/')
#firebasepost = firebase.FirebaseApplication('https://eager-621db.firebaseio.com/VerifiedReports/')

eagerdatabase = firebase.FirebaseApplication('https://eager-621db.firebaseio.com/')
d = {}


@home.route('/')
def homepage():
	print("home page")
	return render_template('home/index.html', title="Welcome")

@home.route('/dashboard')
@login_required
def dashboard():

	queries = Query.query.filter_by(is_admin = True)
	form = QueryForm()
	return render_template('home/dashboard.html', queries = queries, title="Dashboard")


@home.route('/reportissue',methods=['GET', 'POST'])
@login_required
def list_user_issues():
	issues = Issue.query.all()
	subissues = SubIssue.query.all()
	form = IssueForm()
	form.name.choices = [(issue.id,issue.name) for issue in issues]

	if (form.name.data != "None"):
		issue_id = form.name.data

		return redirect(url_for('home.select_sub_issue', id=issue_id))

	return render_template('home/reportissue.html',issues = issues,subissues = subissues,form = form, title = "Report an Issue")


@home.route('/reportissue/selectsubissue/<string:id>',methods=['GET', 'POST'])
@login_required
def select_sub_issue(id):
	subissues = SubIssue.query.filter_by(issue_id = id)
	form = SubIssueForm()
	form.subissue.query = subissues
	form.subissue.choices = [(subissue.id,subissue.name) for subissue in subissues]
	if (form.subissue.data != "None"):
		subissue = request.form['subissue']
		subissue_id = form.subissue.data
		print(subissue_id,subissue)
		additional_info = form.additional_info.data
		send_url = 'http://freegeoip.net/json'
		r = requests.get(send_url)
		j = json.loads(r.text)
		lat = j['latitude']
		lon = j['longitude']
		location = str(lat) + "," + str(lon)
		phone = form.phone.data
		if(carrier._is_mobile(number_type(phonenumbers.parse(phone)))) and phone !='':
			query = Query(employee_id=current_user.id, issue_id =id, subissue_id = subissue_id, additional_info = additional_info, location = location, phone = phone, zip_code = j['zip_code'])
			try:
				db.session.add(query)
				db.session.commit()
				flash('You have successfully added a query')
			except:
				flash('Error: Query already exists.')
		else:
			flash('Please enter a valid contact number')
			return redirect(url_for('home.select_sub_issue', id=id))


		return redirect(url_for('home.list_user_issues'))

	return render_template('home/selectsubissue.html',subissues = subissues,form = form, title = "Select Sub Issue")


@home.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
	reports = eagerdatabase.get('/Reports', None)
	print "Aditya Parmar"


	print "-------------Aditya Parmar-------------"
	for key in reports:
		print key
		print "--data---"
		print reports[key]
		print reports[key]['compactReports']
		print reports[key]['timestamp']
		print reports[key]['longitude']
		print reports[key]['latitude']
		print reports[key]['phoneNumber']
		print reports[key]['type']


	return render_template('home/admin_dashboard.html',reports=reports, title="Admin - Dashboard")


#delete a query
@home.route('/queries/delete/<int:id>', methods = ['GET','POST'])
@login_required
def delete_query(id):
	"""
    Delete a query from the database
    """
	# check_admin()

	deleted_query = Query.query.get_or_404(id)
	db.session.delete(deleted_query)
	db.session.commit()
	flash('You have successfully deleted the query.')

	return redirect(url_for('home.admin_dashboard'))


@home.route('/queries/verify/<int:id>', methods = ['GET','POST'])
@login_required
def verify_query(id):
	"""
	Verify a query
	"""
	# check_admin()
	verified_query = Query.query.get_or_404(id)
	verified_query.is_admin = True
	db.session.commit()
	post = firebasepost.post('/VerifiedReports',{verified_query.issue.name:{0:verified_query.subissue.name, 1:"Additional Info: " + verified_query.additional_info},'phone':verified_query.phone,'latitude':verified_query.location.split(',')[0],'longitude':verified_query.location.split(',')[1]})

	return redirect(url_for('home.admin_dashboard'))

@home.route('/subscribe',methods=['GET', 'POST'])
@login_required
def subscribe():
	"""
	subscribe
	"""
	send_url = 'http://freegeoip.net/json'
	r = requests.get(send_url)
	j = json.loads(r.text)
	flash('Subscribed successfully')
	post = firebasepost.post('/notificationRequests',{'user':current_user.username,'zip code':j['zip_code']})
	return render_template('home/dashboard.html', title="Dashboard")


@home.route('/admin/test', methods=['GET', 'POST'])
def index():
	content = {1:22,4:1}
	return render_template('home/test.html',content = content)
