import web

@web.memoize
def get_db():
    if 'database_url' in web.config:
        return web.database(web.config.database_url)
    else:
        return web.database(**web.config.db_parameters)

class ResultSet:
    """Iterator wrapper over database result.

    Provides utilities like first, list etc.
    """
    def __init__(self, seq, model=web.storage):
        self.model = model
        self.seq = iter(seq)

    def list(self):
        return list(self)

    def __iter__(self):
        return self

    def __next__(self):
        return self.model(next(self.seq))
    next = __next__

    def first(self):
        """Returns the first element from the database result or None.
        """
        try:
            return next(self)
        except StopIteration:
            return None

class Model(web.storage):
    """Base model.
    """
    @classmethod
    def where(cls, **kw):
        result = get_db().where(cls.TABLE, **kw)
        return ResultSet(result, model=cls)

    @classmethod
    def find(cls, **kw):
        """Returns the first item matching the constraints specified as keywords.
        """
        return cls.where(**kw).first()

    @classmethod
    def findall(cls, **kw):
        """Returns the first item matching the constraints specified as keywords.
        """
        return cls.where(**kw).list()

class User(Model):
    TABLE = "users"

    @classmethod
    def new(cls, name, email, phone=None):
        id = get_db().insert("users", name=name, email=email, phone=phone)
        return cls.find(id=id)

class Trainer(Model):
    """Model class for Trainer.
    """
    TABLE = "trainer"

    @classmethod
    def new(cls, name, email, phone, city, **kw):
        id = get_db().insert("users", name=name, email=email, phone=phone)
        get_db().insert('trainer', user_id=id, city=city, seqname=False, **kw)
        return cls.find(id=id)

    @classmethod
    def where(cls, **kw):
        w = 'user_id=users.id'
        if kw:
            w = w + ' AND ' + web.db.sqlwhere(kw)
        result = get_db().select([cls.TABLE, 'users'], what='users.*, trainer.*', where=w)
        return ResultSet(result, model=cls)

    @classmethod
    def update(cls, id, **kw):
        pass
        #get_db().update('trainer', kw, where="user_id=" + str(id))
        #return cls.where(user_id=id)


class Organization(Model):
    TABLE = "organization"
    @classmethod
    def new(cls, name, city, admin_user, role):
        id = get_db().insert("organization", name=name, city=city, admin_id=admin_user.id, admin_role=role)
        return cls.find(id=id)
