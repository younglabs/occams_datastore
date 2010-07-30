import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite

ptc.setupPloneSite()

from zope.app.folder import rootFolder
from zope.app.component.site import SiteManagerContainer, LocalSiteManager
from zope.app.component.site import setSite
from zope.component import getUtility
from zope.interface import verify

import avrc.data.store
from avrc.data.store import interfaces
from avrc.data.store import datastore
from avrc.data.store import model

class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml', avrc.data.store)
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass
    
    def test_implementation(self):
        """
        Tests if the data store implementation has fully objected the interface
        contract
        """
        self.assertTrue(verify.verifyClass(interfaces.IDatastore, 
                                           datastore.Datastore))
    
    def test_multi_site(self):
        """
        Test that the DataStore is able to handle being added to multiple sites
        without mixing the underlying database engines.
        """
        
        root = rootFolder()
        
        root[u"site1"] = site1 = SiteManagerContainer()
        root[u"site2"] = site2 = SiteManagerContainer()
        
        self.assertNotEqual(site1, site2, u"Site containers must be different.")
        
        site1.setSiteManager(LocalSiteManager(site1))
        site2.setSiteManager(LocalSiteManager(site2))
        
        sm1 = site1.getSiteManager()
        sm2 = site2.getSiteManager()
        
        self.assertNotEqual(sm1, sm2, u"Site managers must be different.")
        
        sm1[u"ds"] = datastore.Datastore(pii_dsn=u"sqlite:///:memory:",  
                                        fia_dsn=u"sqlite:///:memory:")
        sm2[u"ds"] = datastore.Datastore(pii_dsn=u"sqlite:///:memory:",  
                                        fia_dsn=u"sqlite:///:memory:") 
    
        self.assertTrue(u"ds" in sm1, u"No datastore found.")
        self.assertTrue(u"ds" in sm2, u"No datastore found.")
        
        setSite(site1)
        SessionFactory = getUtility(interfaces.ISessionFactory)
        Session = SessionFactory()
        
        name = model.Name()
        name.ourid=456
        name.first=u"Foo"
        name.last=u"Bar"
        
        Session.add(name)
        Session.commit()
        
        p = Session.query(model.Name).filter_by(first=u"Foo", last=u"Bar").first()
        self.assertTrue(p is not None, "No person found in first database")
        
        p = Session.query(model.Name).filter_by(first=u"Fuu", last=u"Baz").first()
        self.assertTrue(p is None, "Databases engines are mixed up.")
        
        setSite(site2)
        SessionFactory = getUtility(interfaces.ISessionFactory)
        Session = SessionFactory()
        
        name = model.Name()
        name.ourid=123
        name.first=u"Fuu"
        name.last=u"Baz"
        
        Session.add(name)
        Session.commit()

        p = Session.query(model.Name).filter_by(first=u"Fuu", last=u"Baz").first()
        self.assertTrue(p is not None, "No person found in first database")
        
        p = Session.query(model.Name).filter_by(first=u"Foo", last=u"Bar").first()
        self.assertTrue(p is None, "Databases engines are mixed up.")


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
